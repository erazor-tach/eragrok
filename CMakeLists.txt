set(SOURCES
    src/threshold_types.cpp
    src/db_wrapper.cpp
    src/meal_engine.cpp
    src/food_data.cpp
    src/exercise_data.cpp
    src/utils.cpp
)
# CMakeLists.txt — THRESHOLD C++/JNI Build
# ─────────────────────────────────────────────────────────────────────────────
# Compilation Linux/WSL + Android NDK
# ─────────────────────────────────────────────────────────────────────────────
cmake_minimum_required(VERSION 3.10)
project(threshold_native VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ═════════════════════════════════════════════════════════════════════════════
#  SOURCES
# ═════════════════════════════════════════════════════════════════════════════

set(HEADERS
    include/threshold_types.h
    include/db_wrapper.h
    include/meal_engine.h
    include/utils.h
)

set(SOURCES
    src/threshold_types.cpp
    src/db_wrapper.cpp
    src/meal_engine.cpp
    src/food_data.cpp
    src/exercise_data.cpp
    src/utils.cpp
)

include_directories(${CMAKE_SOURCE_DIR}/include)

# ═════════════════════════════════════════════════════════════════════════════
#  SQLITE3 (Linux : pkg-config)
# ═════════════════════════════════════════════════════════════════════════════

find_package(PkgConfig)
if(PKG_CONFIG_FOUND)
    pkg_check_modules(SQLITE3 sqlite3)
endif()

if(SQLITE3_FOUND)
    message(STATUS "✅ SQLite3 trouvé via pkg-config")
    include_directories(${SQLITE3_INCLUDE_DIRS})
    link_directories(${SQLITE3_LIBRARY_DIRS})
    set(SQLITE3_LIBRARIES ${SQLITE3_LIBRARIES})
else()
    # Fallback : chercher avec find_library
    find_library(SQLITE3_LIB NAMES sqlite3)
    if(SQLITE3_LIB)
        message(STATUS "✅ SQLite3 trouvé : ${SQLITE3_LIB}")
        set(SQLITE3_LIBRARIES ${SQLITE3_LIB})
    else()
        message(FATAL_ERROR "❌ SQLite3 non trouvé. Installer avec : sudo apt install libsqlite3-dev")
    endif()
endif()

# ═════════════════════════════════════════════════════════════════════════════
#  EXÉCUTABLE TEST (standalone)
# ═════════════════════════════════════════════════════════════════════════════

add_executable(threshold_test
    ${SOURCES}
    test/main_test.cpp
)

target_link_libraries(threshold_test PRIVATE ${SQLITE3_LIBRARIES} pthread)

# ═════════════════════════════════════════════════════════════════════════════
#  OPTIONS COMPILATION
# ═════════════════════════════════════════════════════════════════════════════

target_compile_options(threshold_test PRIVATE -Wall -Wextra -O3)

# Mode Release par défaut
if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

message(STATUS "════════════════════════════════════════════════════════════════")
message(STATUS "  Build type : ${CMAKE_BUILD_TYPE}")
message(STATUS "  Compiler   : ${CMAKE_CXX_COMPILER}")
message(STATUS "  SQLite3    : ${SQLITE3_LIBRARIES}")
message(STATUS "════════════════════════════════════════════════════════════════")
