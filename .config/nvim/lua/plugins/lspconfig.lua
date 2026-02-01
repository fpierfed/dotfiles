return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      inlay_hints = {
        enabled = false,
      },
      servers = {
        ty = {
          enabled = false,
        },
        ruff = {
          capabilities = {
            general = {
              positionEncodings = { "utf-16" },
            },
          },
        },
        basedpyright = {
          settings = {
            basedpyright = {
              analysis = {
                typeCheckingMode = "off",
              },
            },
          },
        },
      },
    },
  },
}
