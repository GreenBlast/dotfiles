-- Autocmds are automatically loaded on the VeryLazy event
-- Default autocmds that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/autocmds.lua
-- Add any additional autocmds here

-- vnoremap <C-r> "hy:%s/<C-r>h//gc<left><left><left>
-- vim.api.nvim_set_keymap(
--   "x",
--   "<C-r>",
--   [[:let @h = @*<CR>:%s/<C-r>h//gc<left><left><left>]],
--   { noremap = true, silent = true }
-- )

vim.api.nvim_set_keymap("v", "<C-r>", [["hy:%s/<C-r>h//gc<left><left><left>]], { noremap = true })
