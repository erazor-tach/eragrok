// db_wrapper.cpp — Implémentation SQLite wrapper
// ─────────────────────────────────────────────────────────────────────────────
#include "db_wrapper.h"
#include <stdexcept>
#include <sstream>

namespace threshold {

// ═════════════════════════════════════════════════════════════════════════════
//  DATABASE CONNECTION
// ═════════════════════════════════════════════════════════════════════════════

DatabaseConnection::DatabaseConnection(const std::string& path)
    : db_(nullptr), path_(path), initialized_(false) {
    
    int rc = sqlite3_open(path.c_str(), &db_);
    if (rc != SQLITE_OK) {
        std::string err = "Cannot open database: " + path;
        if (db_) {
            err += " - " + std::string(sqlite3_errmsg(db_));
            sqlite3_close(db_);
            db_ = nullptr;
        }
        throw std::runtime_error(err);
    }
    
    init_pragmas();
    initialized_ = true;
}

DatabaseConnection::~DatabaseConnection() {
    if (db_) {
        sqlite3_close(db_);
        db_ = nullptr;
    }
}

void DatabaseConnection::init_pragmas() {
    execute("PRAGMA journal_mode=WAL");
    execute("PRAGMA foreign_keys=ON");
    execute("PRAGMA synchronous=NORMAL");
}

bool DatabaseConnection::execute(const std::string& sql, std::string* error) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    char* err_msg = nullptr;
    int rc = sqlite3_exec(db_, sql.c_str(), nullptr, nullptr, &err_msg);
    
    if (rc != SQLITE_OK) {
        if (error && err_msg) {
            *error = std::string(err_msg);
        }
        if (err_msg) sqlite3_free(err_msg);
        return false;
    }
    return true;
}

bool DatabaseConnection::query(const std::string& sql,
                               std::function<void(sqlite3_stmt*)> callback,
                               std::string* error) {
    std::lock_guard<std::mutex> lock(mutex_);
    
    sqlite3_stmt* stmt = nullptr;
    int rc = sqlite3_prepare_v2(db_, sql.c_str(), -1, &stmt, nullptr);
    
    if (rc != SQLITE_OK) {
        if (error) *error = sqlite3_errmsg(db_);
        return false;
    }
    
    while ((rc = sqlite3_step(stmt)) == SQLITE_ROW) {
        if (callback) callback(stmt);
    }
    
    sqlite3_finalize(stmt);
    return (rc == SQLITE_DONE);
}

// Helpers DB (stubs — à implémenter module par module)
bool DatabaseConnection::insert_nutrition(const NutritionEntry& entry) {
    // TODO: Implémenter INSERT INTO nutrition
    return false;
}

std::vector<NutritionEntry> DatabaseConnection::get_nutrition_all() {
    // TODO: Implémenter SELECT * FROM nutrition
    return {};
}

std::string DatabaseConnection::get_setting(const std::string& key,
                                            const std::string& default_val) {
    std::string result = default_val;
    std::ostringstream sql;
    sql << "SELECT value FROM settings WHERE key='" << key << "'";
    
    query(sql.str(), [&](sqlite3_stmt* stmt) {
        const char* val = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0));
        if (val) result = val;
    });
    
    return result;
}

bool DatabaseConnection::set_setting(const std::string& key,
                                     const std::string& value) {
    std::ostringstream sql;
    sql << "INSERT OR REPLACE INTO settings (key, value) VALUES ('"
        << key << "', '" << value << "')";
    return execute(sql.str());
}

// ═════════════════════════════════════════════════════════════════════════════
//  DATABASE POOL
// ═════════════════════════════════════════════════════════════════════════════

DatabasePool& DatabasePool::instance() {
    static DatabasePool pool;
    return pool;
}

std::shared_ptr<DatabaseConnection> DatabasePool::get(const std::string& db_path) {
    auto& inst = instance();
    std::lock_guard<std::mutex> lock(inst.pool_mutex_);
    
    auto tid = std::this_thread::get_id();
    auto& thread_pool = inst.pools_[tid];
    
    auto it = thread_pool.find(db_path);
    if (it != thread_pool.end()) {
        return it->second;
    }
    
    // Créer nouvelle connexion
    auto conn = std::make_shared<DatabaseConnection>(db_path);
    thread_pool[db_path] = conn;
    
    // Appliquer migrations
    DatabaseMigrator::apply_migrations(*conn, "user"); // ou "global"
    
    return conn;
}

void DatabasePool::close_all() {
    auto& inst = instance();
    std::lock_guard<std::mutex> lock(inst.pool_mutex_);
    inst.pools_.clear(); // shared_ptr → destructeurs auto
}

// ═════════════════════════════════════════════════════════════════════════════
//  MIGRATIONS (constantes SQL — à remplir depuis Python migrations/)
// ═════════════════════════════════════════════════════════════════════════════

const char* DatabaseMigrator::USER_001_INITIAL = R"SQL(
-- Migration user_001_initial.sql
CREATE TABLE IF NOT EXISTS nutrition (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    poids REAL,
    age INTEGER,
    calories TEXT,
    proteines TEXT,
    glucides TEXT,
    lipides TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS planning (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    groupes TEXT,
    programme TEXT,
    types TEXT,
    note TEXT,
    line TEXT,
    exercises TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
)SQL";

const char* DatabaseMigrator::GLOBAL_001_INITIAL = R"SQL(
-- Migration global_001_initial.sql (porté depuis Python)
CREATE TABLE IF NOT EXISTS users (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    name           TEXT    NOT NULL UNIQUE,
    age            TEXT    DEFAULT '',
    date_naissance TEXT    DEFAULT '',
    sexe           TEXT    DEFAULT 'Homme',
    taille         TEXT    DEFAULT '',
    poids          TEXT    DEFAULT '',
    objectif       TEXT    DEFAULT '',
    ajustement     TEXT    DEFAULT 'Maintien (0%)'
);
)SQL";

bool DatabaseMigrator::apply_migrations(DatabaseConnection& db,
                                        const std::string& type) {
    db.execute(R"SQL(
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version TEXT PRIMARY KEY,
            applied_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    )SQL");
    
    if (type == "global") {
        if (!has_migration(db, "global_001_initial")) {
            if (!db.execute(GLOBAL_001_INITIAL)) return false;
            mark_migration(db, "global_001_initial");
        }
    } else {
        if (!has_migration(db, "user_001_initial")) {
            if (!db.execute(USER_001_INITIAL)) return false;
            mark_migration(db, "user_001_initial");
        }
    }
    
    return true;
}

bool DatabaseMigrator::has_migration(DatabaseConnection& db,
                                     const std::string& version) {
    bool exists = false;
    std::ostringstream sql;
    sql << "SELECT 1 FROM schema_migrations WHERE version='" << version << "'";
    db.query(sql.str(), [&](sqlite3_stmt*) { exists = true; });
    return exists;
}

bool DatabaseMigrator::mark_migration(DatabaseConnection& db,
                                      const std::string& version) {
    std::ostringstream sql;
    sql << "INSERT INTO schema_migrations (version) VALUES ('" << version << "')";
    return db.execute(sql.str());
}

// ═════════════════════════════════════════════════════════════════════════════
//  USER PROFILE CRUD
// ═════════════════════════════════════════════════════════════════════════════

bool DatabaseConnection::add_user(const UserProfile& p) {
    std::string dn = p.date_naissance;
    int age_val = age_depuis_naissance(dn);
    std::string age_str = (age_val > 0) ? std::to_string(age_val) : "";
    
    std::ostringstream sql;
    sql << "INSERT INTO users (name,age,date_naissance,sexe,taille,poids,objectif,ajustement) "
        << "VALUES ('" << json_escape(p.nom) << "','" << age_str << "','"
        << json_escape(dn) << "','" << json_escape(p.sexe) << "','"
        << p.taille << "','" << p.poids << "','"
        << json_escape(p.objectif) << "','" << json_escape(p.ajustement) << "')";
    return execute(sql.str());
}

bool DatabaseConnection::update_user(const std::string& old_name, const UserProfile& p) {
    std::string dn = p.date_naissance;
    int age_val = age_depuis_naissance(dn);
    std::string age_str = (age_val > 0) ? std::to_string(age_val) : "";

    std::lock_guard<std::mutex> lock(mutex_);
    sqlite3_stmt* stmt = nullptr;
    const char* sql = "UPDATE users SET name=?,age=?,date_naissance=?,sexe=?,taille=?,poids=?,objectif=?,ajustement=? WHERE name=?";
    int rc = sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr);
    if (rc != SQLITE_OK) return false;
    sqlite3_bind_text(stmt, 1, p.nom.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, age_str.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 3, dn.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 4, p.sexe.c_str(), -1, SQLITE_TRANSIENT);
    std::string t_str = std::to_string(p.taille);
    std::string p_str = std::to_string(p.poids);
    sqlite3_bind_text(stmt, 5, t_str.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 6, p_str.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 7, p.objectif.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 8, p.ajustement.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 9, old_name.c_str(), -1, SQLITE_TRANSIENT);
    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return (rc == SQLITE_DONE && sqlite3_changes(db_) > 0);
}

bool DatabaseConnection::delete_user(const std::string& name) {
    std::ostringstream sql;
    sql << "DELETE FROM users WHERE name='" << json_escape(name) << "'";
    return execute(sql.str());
}

UserProfile DatabaseConnection::get_user(const std::string& name) {
    UserProfile p;
    // Use prepared statement to avoid SQL injection / quoting issues
    std::lock_guard<std::mutex> lock(mutex_);
    sqlite3_stmt* stmt = nullptr;
    int rc = sqlite3_prepare_v2(db_, "SELECT * FROM users WHERE name=?", -1, &stmt, nullptr);
    if (rc != SQLITE_OK) return p;
    sqlite3_bind_text(stmt, 1, name.c_str(), -1, SQLITE_TRANSIENT);
    if (sqlite3_step(stmt) == SQLITE_ROW) {
        auto col = [&](int i) -> std::string {
            const char* v = reinterpret_cast<const char*>(sqlite3_column_text(stmt, i));
            return v ? v : "";
        };
        p.nom            = col(1);
        p.date_naissance = col(3);
        p.sexe           = col(4);
        p.taille         = parse_float(col(5));
        p.poids          = parse_float(col(6));
        p.objectif       = col(7);
        p.ajustement     = col(8);
        p.age            = age_depuis_naissance(p.date_naissance);
        p.folder         = to_folder_name(p.nom);
    }
    sqlite3_finalize(stmt);
    return p;
}

std::vector<std::string> DatabaseConnection::list_users() {
    std::vector<std::string> result;
    query("SELECT name FROM users ORDER BY id ASC", [&](sqlite3_stmt* stmt) {
        const char* v = reinterpret_cast<const char*>(sqlite3_column_text(stmt, 0));
        if (v) result.push_back(v);
    });
    return result;
}

// ═════════════════════════════════════════════════════════════════════════════
//  PLANNING CRUD (table planning — DB utilisateur)
// ═════════════════════════════════════════════════════════════════════════════

bool DatabaseConnection::add_planning(const std::string& date, const std::string& groupes,
                                      const std::string& programme, const std::string& types,
                                      const std::string& note, const std::string& line,
                                      const std::string& exercises_json) {
    std::lock_guard<std::mutex> lock(mutex_);
    sqlite3_stmt* stmt = nullptr;
    const char* sql = "INSERT INTO planning (date,groupes,programme,types,note,line,exercises) VALUES (?,?,?,?,?,?,?)";
    int rc = sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr);
    if (rc != SQLITE_OK) return false;
    sqlite3_bind_text(stmt, 1, date.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, groupes.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 3, programme.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 4, types.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 5, note.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 6, line.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 7, exercises_json.c_str(), -1, SQLITE_TRANSIENT);
    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return (rc == SQLITE_DONE);
}

bool DatabaseConnection::update_planning(int64_t id, const std::string& groupes,
                                         const std::string& programme,
                                         const std::string& exercises_json,
                                         const std::string& note) {
    std::lock_guard<std::mutex> lock(mutex_);
    sqlite3_stmt* stmt = nullptr;
    const char* sql = "UPDATE planning SET groupes=?,programme=?,exercises=?,note=? WHERE id=?";
    int rc = sqlite3_prepare_v2(db_, sql, -1, &stmt, nullptr);
    if (rc != SQLITE_OK) return false;
    sqlite3_bind_text(stmt, 1, groupes.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, programme.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 3, exercises_json.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 4, note.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_int64(stmt, 5, id);
    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return (rc == SQLITE_DONE && sqlite3_changes(db_) > 0);
}

bool DatabaseConnection::delete_planning(int64_t id) {
    std::lock_guard<std::mutex> lock(mutex_);
    sqlite3_stmt* stmt = nullptr;
    int rc = sqlite3_prepare_v2(db_, "DELETE FROM planning WHERE id=?", -1, &stmt, nullptr);
    if (rc != SQLITE_OK) return false;
    sqlite3_bind_int64(stmt, 1, id);
    rc = sqlite3_step(stmt);
    sqlite3_finalize(stmt);
    return (rc == SQLITE_DONE && sqlite3_changes(db_) > 0);
}

static PlanningEntry parse_planning_row(sqlite3_stmt* stmt) {
    auto col = [&](int i) -> std::string {
        const char* v = reinterpret_cast<const char*>(sqlite3_column_text(stmt, i));
        return v ? v : "";
    };
    PlanningEntry e;
    e.id        = sqlite3_column_int64(stmt, 0);
    e.date      = col(1);
    e.groupes   = col(2);
    e.programme = col(3);
    e.types     = col(4);
    e.note      = col(5);
    e.line      = col(6);
    e.exercises = col(7);
    return e;
}

std::vector<PlanningEntry> DatabaseConnection::get_planning_by_date(const std::string& date) {
    std::vector<PlanningEntry> result;
    std::lock_guard<std::mutex> lock(mutex_);
    sqlite3_stmt* stmt = nullptr;
    int rc = sqlite3_prepare_v2(db_, "SELECT * FROM planning WHERE date=? ORDER BY id ASC", -1, &stmt, nullptr);
    if (rc != SQLITE_OK) return result;
    sqlite3_bind_text(stmt, 1, date.c_str(), -1, SQLITE_TRANSIENT);
    while (sqlite3_step(stmt) == SQLITE_ROW) result.push_back(parse_planning_row(stmt));
    sqlite3_finalize(stmt);
    return result;
}

std::vector<PlanningEntry> DatabaseConnection::get_planning_range(const std::string& start,
                                                                   const std::string& end) {
    std::vector<PlanningEntry> result;
    std::lock_guard<std::mutex> lock(mutex_);
    sqlite3_stmt* stmt = nullptr;
    int rc = sqlite3_prepare_v2(db_, "SELECT * FROM planning WHERE date>=? AND date<=? ORDER BY date ASC, id ASC", -1, &stmt, nullptr);
    if (rc != SQLITE_OK) return result;
    sqlite3_bind_text(stmt, 1, start.c_str(), -1, SQLITE_TRANSIENT);
    sqlite3_bind_text(stmt, 2, end.c_str(), -1, SQLITE_TRANSIENT);
    while (sqlite3_step(stmt) == SQLITE_ROW) result.push_back(parse_planning_row(stmt));
    sqlite3_finalize(stmt);
    return result;
}

} // namespace threshold
