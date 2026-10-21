-- Personal markdownlint rules for every Markdown buffer, in any directory.
--
-- Why this file has to exist: nvim-lint pipes the buffer to
-- `markdownlint-cli2 -` over stdin, so there is no file path to resolve config
-- from, and markdownlint-cli2 only searches for a config from its cwd upward —
-- never above it, and there is no ~/.markdownlintrc-style global. So with nvim
-- started anywhere other than a directory holding a config, you get the stock
-- 80-column defaults. Passing --config fixes that everywhere.
--
-- A project's own .markdownlint.yaml still wins: a directory config is layered
-- on top of whatever --config supplies.

local vault = vim.fn.expand("~/Dropbox/sarcophagus/Obsidian/Aviad")
local dir = vim.fn.expand("~/.config/markdownlint")

-- Picked per buffer, not per cwd, so the vault rules apply even with nvim
-- opened deep inside the vault, and never apply to a repo outside it.
local function config_for(bufnr)
  local path = vim.api.nvim_buf_get_name(bufnr or 0)
  if path:sub(1, #vault + 1) == vault .. "/" then
    return dir .. "/vault.markdownlint.yaml"
  end
  return dir .. "/default.markdownlint.yaml"
end

return {
  -- Diagnostics.
  {
    "mfussenegger/nvim-lint",
    optional = true,
    opts = {
      linters = {
        ["markdownlint-cli2"] = {
          args = {
            "--config",
            function()
              return config_for(vim.api.nvim_get_current_buf())
            end,
            "-",
          },
        },
      },
    },
  },

  -- Format-on-save runs `markdownlint-cli2 --fix`; it needs the same rules, or
  -- it would "fix" files against defaults these configs deliberately turn off.
  {
    "stevearc/conform.nvim",
    optional = true,
    opts = {
      formatters = {
        ["markdownlint-cli2"] = {
          prepend_args = function(_, ctx)
            return { "--config", config_for(ctx.buf) }
          end,
        },
      },
    },
  },
}
