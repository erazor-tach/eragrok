// db_wrapper.h — Wrapper SQLite thread-safe pour THRESHOLD
// ─────────────────────────────────────────────────────────────────────────────
// Pool de connexions par thread (comme Python db.py)
// Compatible Android NDK + SQLite3
// ─────────────────────────────────────────────────────────────────────────────
#ifndef THRESHOLD_DB_WRAPPER_H
#define THRESHOLD_DB_WRAPPER_H

#include "threshold_types.h"
#include "utils.h"
#include <sqlite3.h>
#include <mutex>
#include <thread>
#include <unordered_map>
#include <functional>

namespace threshold {

// ═════════════════════════════════════════════════════════════════════════════
//  POOL DE CONNEXIONS THREAD-LOCAL
// ═════════════════════════════════════════════════════════════════════════════

class DatabaseConnection {
private:
    sqlite3* db_;
    std::mutex mutex_;
    std::string path_;
    bool initialized_;
    
    void init_pragmas();
    
public:
    DatabaseConnection(const std::string& path);
    ~DatabaseConnection();
    
    // Exécution requête (thread-safe)
    bool execute(const std::string& sql, std::string* error = nullptr);
    
    // Query avec callback par ligne
    bool query(const std::string& sql,
               std::function<void(sqlite3_stmt*)> callback,
               std::string* error = nullptr);
    
    // Helpers types
    bool insert_nutrition(const NutritionEntry& entry);
    bool insert_cycle(const CycleEntry& entry);
    
    std::vector<NutritionEntry> get_nutrition_all();
    CycleEntry get_cycle_active();
    
    // Settings
    std::string get_setting(const std::string& key, const std::string& default_val = "");
    bool set_setting(const std::string& key, const std::string& value);
    
    // User Profile CRUD (table users dans DB globale)
    bool add_user(const UserProfile& profile);
    bool update_user(const std::string& old_name, const UserProfile& profile);
    bool delete_user(const std::string& name);
    UserProfile get_user(const std::string& name);
    std::vector<std::string> list_users();
    
    // Planning CRUD (table planning dans DB utilisateur)
    bool add_planning(const std::string& date, const std::string& groupes,
                      const std::string& programme, const std::string& types,
                      const std::string& note, const std::string& line,
                      const std::string& exercises_json);
    bool update_planning(int64_t id, const std::string& groupes,
                         const std::string& programme, const std::string& exercises_json,
                         const std::string& note);
    bool delete_planning(int64_t id);
    std::vector<PlanningEntry> get_planning_by_date(const std::string& date);
    std::vector<PlanningEntry> get_planning_range(const std::string& start,
                                                    const std::string& end);
    
    sqlite3* raw() { return db_; } // Access bas niveau si besoin
};

// ═════════════════════════════════════════════════════════════════════════════
//  POOL GLOBAL THREAD-SAFE
// ═════════════════════════════════════════════════════════════════════════════

class DatabasePool {
private:
    std::mutex pool_mutex_;
    std::unordered_map<std::thread::id,
                       std::unordered_map<std::string,
                                          std::shared_ptr<DatabaseConnection>>> pools_;
    
    static DatabasePool& instance();
    
public:
    static std::shared_ptr<DatabaseConnection> get(const std::string& db_path);
    static void close_all(); // Cleanup (appelé depuis JNI OnUnload)
};

// ═════════════════════════════════════════════════════════════════════════════
//  MIGRATIONS SCHÉMA (portées depuis Python data/migrations/)
// ═════════════════════════════════════════════════════════════════════════════

class DatabaseMigrator {
public:
    static bool apply_migrations(DatabaseConnection& db, const std::string& type);
    
private:
    static const char* GLOBAL_001_INITIAL;
    static const char* USER_001_INITIAL;
    static const char* USER_002_CYCLE_COLUMNS;
    static const char* USER_003_CUSTOM_PRODUCTS;
    static const char* USER_004_CUSTOM_FOOD;
    static const char* USER_005_EXERCISES_PLANNING;
    static const char* USER_006_PREFERENCES;
    
    static bool has_migration(DatabaseConnection& db, const std::string& version);
    static bool mark_migration(DatabaseConnection& db, const std::string& version);
};

} // namespace threshold

#endif // THRESHOLD_DB_WRAPPER_H
