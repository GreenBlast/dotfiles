return {
  "Exafunction/codeium.vim",
  event = "BufEnter",
  -- Enable Codeium only on machines that are actually authenticated. Without an
  -- apiKey the language server hangs nvim on startup (and this config is shared
  -- across machines). The key lives in <codeium-home>/config.json, written by
  -- `:Codeium Auth`; codeium#command#HomeDir() resolves it as below. On an
  -- authenticated machine the file exists -> Codeium enabled and works normally.
  init = function()
    local xdg = vim.env.XDG_DATA_HOME
    local home = (xdg and xdg ~= "") and (xdg .. "/.codeium") or (vim.env.HOME .. "/.codeium")
    vim.g.codeium_enabled = vim.fn.filereadable(home .. "/config.json") == 1
  end,
  config = function()
    -- Change '<C-g>' here to any keycode you like.
    vim.keymap.set("i", "<C-g>", function()
      return vim.fn["codeium#Accept"]()
    end, { expr = true })
    -- lets add more keybinding for other codeium functions:
    vim.keymap.set("i", "<c-;>", function()
      return vim.fn["codeium#CycleCompletions"](1)
    end, { expr = true })
    vim.keymap.set("i", "<c-,>", function()
      return vim.fn["codeium#CycleCompletions"](-1)
    end, { expr = true })
    vim.keymap.set("i", "<c-x>", function()
      return vim.fn["codeium#Clear"]()
    end, { expr = true })
    vim.keymap.set("i", "<c-s>", function()
      return vim.fn["codeium#Force"]()
    end, { expr = true })
  end,
}
