-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
--
-- Add any additional autocmds here
-- with `vim.api.nvim_create_autocmd`
--
-- Or remove existing autocmds by their group name (which is prefixed with `lazyvim_` for the defaults)
-- e.g. vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")

-- Do not start a new line with a comment if the current line is a comment.
vim.api.nvim_create_autocmd("FileType", {
  pattern = "*",
  callback = function()
    vim.opt_local.formatoptions:remove({ "r", "o" })
  end,
})

-- Custom highlight overrides. Re-applied on ColorScheme since the theme
-- redefines these groups whenever it (re)loads.
local function apply_highlights()
  vim.api.nvim_set_hl(0, "ColorColumn", { ctermbg = 254, bg = "#eaeef2" })
  -- Recolor render-markdown.nvim's code backgrounds.
  vim.api.nvim_set_hl(0, "RenderMarkdownCode", { bg = "#f6f8fa" })
  vim.api.nvim_set_hl(0, "RenderMarkdownCodeInline", { bg = "#f6f8fa" })
end

vim.api.nvim_create_autocmd("ColorScheme", {
  group = vim.api.nvim_create_augroup("custom_highlights", { clear = true }),
  callback = apply_highlights,
})
-- Apply now for the already-loaded colorscheme.
apply_highlights()
