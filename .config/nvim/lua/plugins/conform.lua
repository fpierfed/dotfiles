return {
  "stevearc/conform.nvim",
  optional = true,
  opts = {
    formatters_by_ft = {
      -- markdown = { "markdownlint-cli2" },
      python = { "ruff_fix", "ruff_organize_imports", "ruff_format" },
      lua = { "stylua" },
      fish = { "fish_indent" },
      sh = { "shfmt" },
      markdown = { "prettier", "markdownlint-cli2", "markdown-toc" },
      ["markdown.mdx"] = { "prettier", "markdownlint-cli2", "markdown-toc" },
    },
    formatters = {},
  },
}
