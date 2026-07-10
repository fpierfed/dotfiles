return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      inlay_hints = { enabled = false },
      servers = {
        -- NOTE: disable pyright/basedpyright to enable ruff linting/formating
        pyright = {
          enabled = false,
          settings = {
            pyright = {
              typeCheckingMode = "off",
              -- Using Ruff's import organizer
              disableOrganizeImports = true,
            },
            python = {
              analysis = {
                -- Ignore all files for analysis to exclusively use Ruff for linting
                ignore = { "*" },
              },
            },
          },
        },
        -- Enable ty astral mypy alternative
        ty = {
          enabled = false,
          settings = {
            ty = {
              configuration = {
                rules = {
                  ["unresolved-reference"] = "warn",
                },
              },
            },
          },
        },
        basedpyright = {
          settings = {
            basedpyright = {
              analysis = {
                typeCheckingMode = "off",
                ignore = { "*" },
              },
              disableOrganizeImports = true,
            },
          },
        },
        ruff = {
          capabilities = {
            general = {
              positionEncodings = { "utf-16" },
            },
          },
          init_options = {
            settings = {
              diagnostics = true,
              lineLength = 79,
              fixAll = true, -- Enable auto-fix for all violations
              organizeImports = true, -- Explicitly enable import organization
              lint = {
                -- select = { "ALL" },
                ignore = {
                  "B010",
                  "E202",
                  "D202",
                  "D212",
                  "D203",
                  "D211",
                  "D213",
                  "W191",
                  "E111",
                  "E114",
                  "E117",
                  "D206",
                  "D300",
                  "Q000",
                  "Q001",
                  "Q002",
                  "Q003",
                  "COM812",
                  "COM819",
                  "CPY001",
                  "ISC001",
                  "TD002",
                  "TD003",
                  "E501",
                },
              },
            },
          },
        },
      },
      diagnostics = {
        underline = true,
        update_in_insert = true,
        virtual_text = true,
        float = {
          source = "always", -- show diagnostic source in float
          border = "rounded",
        },
      },
    },
  },
}
