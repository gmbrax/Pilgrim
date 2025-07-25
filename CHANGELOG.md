# Changelog

All notable changes to this project will be documented in this file.
The format is based on Keep a Changelog, and this project adheres to Semantic Versioning.

## Unreleased

## Planned
* Restore from backup functionality
* Organization of trips by date, location, or theme
* Enhanced photo management features
* Search functionality
* Export features
* UI Testing with Textual Pilot

## [0.0.5] - 2025-07-24

### Added
* **Backup Feature:** Introduced a full backup feature to export the database and all photos to a single ZIP file.
* **Diary Settings Screen:** Added a dedicated settings screen per diary, accessible with the 's' key from the diary list.
* **Advanced Deletion Options:** The new settings screen allows for deleting the entire diary, all of its entries, or all of its photos.
* **Confirmation Modals:** Added confirmation modals that require the user to type the diary's name to proceed with critical delete operations, preventing accidental data loss.
* **Comprehensive Test Suite:** Implemented a robust unit and integration test suite for the entire backend (services, models, utils, application), achieving high code coverage and ensuring stability.

### Changed
* **Architectural Refactor:** Service methods were refactored to be transactional, allowing for more complex operations to be executed safely and atomically.
* **Configuration:** The "auto-open diary on startup" setting is now managed and persisted via the `config.toml` file.
* **Project Structure:** Standardized project metadata and build configuration in `pyproject.toml` and converted all imports to use a consistent absolute path structure.

### Fixed
* **Directory Name Sanitization:** Fixed a bug where directory names were not correctly sanitized, now properly handling accented and special characters by using transliteration.
* **Data Integrity:** Enforced `NOT NULL` constraints on `title` and `date` fields for entries in the database, preventing the creation of entries with invalid data.

### Removed
* **Obsolete Mocks:** Removed old and unused mock service files from the production codebase.

## [0.0.4] - 2025-07-19

### Added
* Support for creating new diaries asynchronously, with an option to automatically open the newly created diary.
* Unified "Enter" key support for saving or creating diaries across relevant modals.
* Automatic diary list refresh when returning to the diary screen.
* Application configuration management with a new centralized config system.
* Database location and initialization now configurable via the new config manager.
* Automatic migration of database file to the configuration directory.
* Display of database URL on application startup for transparency.
* Duplicate photo detection before photo creation to prevent redundant entries.
* Photo hash indexing to improve photo lookup performance.

### Changed
* Enhanced feedback and validation when editing or creating diary names.
* Streamlined and unified save logic for diary modals, reducing duplicated behavior.
* About screen now displays the actual installed application version dynamically.
* Sidebar and photo-related UI text updated to remove emoji icons for a cleaner appearance.
* Sidebar layout and scrolling behavior improved for better usability.
* Photo hash generation now relies on existing service-provided hashes instead of local computation.

### Improved
* Enhanced feedback and validation when editing or creating diary names.
* Streamlined and unified save logic for diary modals, reducing duplicated behavior.
* Sidebar layout and scrolling behavior for better usability.

## [0.0.3] - 2025-07-07

### Changed
* Removed the dependency on textual-dev from pyproject.toml.

## [0.0.2] - 2025-07-07

### Changed
* Changed the license in pyproject.toml to BSD.

## [0.0.1] - 2025-07-06

### Added
* Initial alpha release of Pilgrim travel diary application.
* Create and edit travel diaries.
* Create and edit diary entries.
* Photo ingestion system.
* Photo addition and reference via sidebar.
* Text User Interface (TUI) built with Textual framework.
* Pre-compiled binary installation method (Method 2).
* Support for Linux operating systems.
* Basic project documentation (README).

### Known Issues
* Installation Method 1 not yet implemented.
* No testing suite implemented yet.
* Some features may be unstable in an alpha version.
