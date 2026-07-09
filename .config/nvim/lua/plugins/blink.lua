local function in_comment()
  local row, col = unpack(vim.api.nvim_win_get_cursor(0))
  local parser = vim.treesitter.get_parser(0)
  if not parser then
    return false
  end
  parser:parse()
  local node = vim.treesitter.get_node({ pos = { row - 1, math.max(0, col - 1) } })
  if not node then
    return false
  end
  while node do
    if node:type() == "comment" then
      return true
    end
    node = node:parent()
  end
  return false
end

return {
  "saghen/blink.cmp",
  -- Function form: lazy.nvim *concatenates* list fields when merging opts tables,
  -- which would re-add "buffer". Assigning inside a function replaces it cleanly.
  opts = function(_, opts)
    -- Drop the "buffer" source (word-scraping from open buffers); keep semantic sources only.
    opts.sources = opts.sources or {}
    opts.sources.default = { "lsp", "path" }

    opts.enabled = function()
      local ft = vim.bo.filetype
      if ft == "markdown" or ft == "text" then
        return false
      end
      return not in_comment()
    end

    opts.completion = vim.tbl_deep_extend("force", opts.completion or {}, {
      list = {
        max_items = 10,
      },
      trigger = {
        show_in_snippet = false,
      },
      menu = {
        auto_show = false,
        border = "rounded",
      },
      documentation = {
        auto_show = true,
        window = { border = "rounded" },
      },
      ghost_text = {
        enabled = function()
          return not in_comment()
        end,
        show_without_selection = true,
        show_with_menu = false,
      },
    })
  end,
}
