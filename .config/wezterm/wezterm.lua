local wezterm = require("wezterm")
local config = wezterm.config_builder()
local act = wezterm.action

config.initial_cols = 120
config.initial_rows = 28

config.font = wezterm.font("BlexMono Nerd Font Mono")
config.font_size = 14
config.freetype_load_target = "Light"
config.freetype_render_target = "HorizontalLcd"

config.color_scheme = "Github (base16)"

config.quit_when_all_windows_are_closed = false

config.audible_bell = "Disabled"
config.visual_bell = {
	fade_in_function = "EaseIn",
	fade_in_duration_ms = 100,
}
config.colors = {
	visual_bell = "#f00000",
}

config.keys = {
	-- macos line movements
	{ key = "RightArrow", mods = "OPT", action = act({ SendString = "\x1bf" }) },
	{ key = "LeftArrow", mods = "OPT", action = act({ SendString = "\x1bb" }) },

	-- map cmd+k combine : clear_terminal scroll active : clear_terminal scrollback active
	{ key = "k", mods = "CMD", action = act.ClearScrollback("ScrollbackAndViewport") },
	-- map cmd+right next_tab
	{ key = "RightArrow", mods = "CMD", action = act.ActivateTabRelative(1) },
	-- map cmd+left previous_tab
	{ key = "LeftArrow", mods = "CMD", action = act.ActivateTabRelative(-1) },
	-- map cmd+shift+right move_tab_forward
	{ key = "RightArrow", mods = "CMD|SHIFT", action = act.MoveTabRelative(1) },
	-- map cmd+shift+left move_tab_backward
	{ key = "LeftArrow", mods = "CMD|SHIFT", action = act.MoveTabRelative(-1) },
	-- map cmd+d launch --cwd=current --location=vsplit
	{ key = "d", mods = "CMD", action = act.SplitHorizontal },
	-- map cmd+shift+d launch --cwd=current --location=hsplit
	{ key = "d", mods = "SHIFT|CMD", action = act.SplitVertical },
	-- map cmd+alt+right neighboring_pane right
	{ key = "RightArrow", mods = "CMD|OPT", action = act.ActivatePaneDirection("Right") },
	-- map cmd+alt+left neighboring_pane left
	{ key = "LeftArrow", mods = "CMD|OPT", action = act.ActivatePaneDirection("Left") },
	-- map cmd+alt+up neighboring_pane up
	{ key = "UpArrow", mods = "CMD|OPT", action = act.ActivatePaneDirection("Up") },
	-- map cmd+alt+down neighboring_pane down
	{ key = "DownArrow", mods = "CMD|OPT", action = act.ActivatePaneDirection("Down") },
	-- Swap panes around
	{
		key = "p",
		mods = "CMD|ALT|CTRL",
		action = act.PaneSelect({ mode = "SwapWithActiveKeepFocus", alphabet = "123456789" }),
	},
	-- map cmd+ctrl+left resize_pane narrower
	{ key = "LeftArrow", mods = "CMD|CTRL", action = act.AdjustPaneSize({ "Left", 1 }) },
	-- map cmd+ctrl+right resize_pane wider
	{ key = "RightArrow", mods = "CMD|CTRL", action = act.AdjustPaneSize({ "Right", 1 }) },
	-- map cmd+ctrl+up resize_pane taller
	{ key = "UpArrow", mods = "CMD|CTRL", action = act.AdjustPaneSize({ "Up", 1 }) },
	-- map cmd+ctrl+down resize_pane shorter
	{ key = "DownArrow", mods = "CMD|CTRL", action = act.AdjustPaneSize({ "Down", 1 }) },
}

-- Plugins
local tabline = wezterm.plugin.require("https://github.com/michaelbrusegard/tabline.wez")
tabline.setup({
	options = {
		icons_enabled = true,
		theme = "Github (base16)",
		tabs_enabled = false,
		theme_overrides = {},
		section_separators = {
			left = wezterm.nerdfonts.pl_left_hard_divider,
			right = wezterm.nerdfonts.pl_right_hard_divider,
		},
		component_separators = {
			left = wezterm.nerdfonts.pl_left_soft_divider,
			right = wezterm.nerdfonts.pl_right_soft_divider,
		},
		tab_separators = {
			left = wezterm.nerdfonts.pl_left_hard_divider,
			right = wezterm.nerdfonts.pl_right_hard_divider,
		},
	},
	sections = {
		tabline_a = { "mode" },
		tabline_b = { "workspace" },
		tabline_c = { " " },
		tab_active = {
			"index",
			{ "parent", padding = 0 },
			"/",
			{ "cwd", padding = { left = 0, right = 1 } },
			{ "zoomed", padding = 0 },
		},
		tab_inactive = { "index", { "process", padding = { left = 0, right = 1 } } },
		tabline_x = { "ram", "cpu" },
		tabline_y = { "datetime", "battery" },
		tabline_z = { "domain" },
	},
	extensions = {},
})
tabline.apply_to_config(config)

config.window_decorations = "TITLE|RESIZE"

-- Finally, return the configuration to wezterm:
return config
