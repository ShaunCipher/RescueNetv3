class Theme:
    # --- Backgrounds ---
    BG_DARKER = "#181818"    # Side panels / Terminal
    BG_DARK   = "#1a1a1a"    # PanedWindow sashes
    BG_MAIN   = "#212121"    # Main Workspace (Map area)
    NAV_BG    = "#121212"    # Top Navigation (slightly darker for contrast)

    # --- Accents & Branding ---
    RESCUE_GREEN = "#32CD32"  # Primary Identity Color
    ACCENT_BLUE  = "#1F6AA5"  # Secondary (for buttons/highlights)
    
    # --- Status Colors (For Terminal Logs) ---
    LOG_INFO    = "#32CD32"   # Green
    LOG_WARNING = "#FFA500"   # Orange
    LOG_ERROR   = "#FF4B4B"   # Red

    # --- Text & Borders ---
    TEXT_MAIN  = "#FFFFFF"    # Primary Text
    TEXT_DIM   = "#888888"    # Subtitles / Header Labels
    BORDER_ALL = "#2B2B2B"    # Component Borders
    BORDER_GRAY = "#333333"
    HOVER_GRAY = "#3d3d3d"    # Button Hover state

    # --- Component Specifics ---
    SASH_COLOR = BG_DARK
    TERMINAL_TEXT = RESCUE_GREEN