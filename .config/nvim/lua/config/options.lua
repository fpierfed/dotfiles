-- Options are automatically loaded before lazy.nvim startup
-- Default options that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/options.lua
-- Add any additional options here
vim.g.lazyvim_python_lsp = "basedpyright"
vim.g.lazyvim_python_ruff = "ruff"

-- Disable mouse mode
vim.opt.mouse = ""
vim.opt.mousescroll = "ver:0,hor:0"
-- Do not center the cursor horizontally!
vim.opt.sidescrolloff = 0
vim.opt.sidescroll = 0

-- Disable autopairs (via mini.nvim / mini.pairs)
vim.b.minipairs_disable = true
