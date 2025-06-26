-- Keymaps are automatically loaded on the VeryLazy event
-- Default keymaps that are always set: https://github.com/LazyVim/LazyVim/blob/main/lua/lazyvim/config/keymaps.lua
-- Add any additional keymaps here

vim.keymap.set("i", "jk", "<Esc>")

vim.keymap.set("n", "-", "<CMD>Oil<CR>", { desc = "Open parent directory" })

-- #### From the ThePrimeagen dotfiles https://github.com/ThePrimeagen/init.lua remap.lua

-- Move lines in Visual mode - Not Tested
vim.keymap.set("v", "J", ":m '>+1<CR>gv=gv")
vim.keymap.set("v", "K", ":m '<-2<CR>gv=gv")

-- When using J to delete line breaks - cursor will stay in place
vim.keymap.set("n", "J", "mzJ`z")

-- When scrolling up and down the screen will stay in center - Not Tested
vim.keymap.set("n", "<C-d>", "<C-d>zz")
vim.keymap.set("n", "<C-u>", "<C-u>zz")

-- When going in search results up and down the screen will stay in center - Not Tested
vim.keymap.set("n", "n", "nzzzv")
vim.keymap.set("n", "N", "Nzzzv")

-- Leader p will paste without saving into the clipboard
vim.keymap.set("x", "<leader>p", [["_dP]])

-- Leader y will save saving into the clipboard
vim.keymap.set({ "n", "v" }, "<leader>y", [["+y]])
vim.keymap.set("n", "<leader>Y", [["+Y]])

-- Leader p will delete without saving into the clipboard
vim.keymap.set({ "n", "v" }, "<leader>d", [["_d]])

-- Go over lists of errors and changes - Not Tested
vim.keymap.set("n", "<C-k>", "<cmd>cnext<CR>zz")
vim.keymap.set("n", "<C-j>", "<cmd>cprev<CR>zz")
vim.keymap.set("n", "<leader>k", "<cmd>lnext<CR>zz")
vim.keymap.set("n", "<leader>j", "<cmd>lprev<CR>zz")

-- Switch tmux sessions - Not Tested
-- vim.keymap.set("n", "<C-f>", "<cmd>silent !tmux neww tmux-sessionizer<CR>")

-- Making current file executable
vim.keymap.set("n", "<leader>x", "<cmd>!chmod +x %<CR>", { silent = true })

vim.keymap.set("n", "<leader>mr", "<cmd>CellularAutomaton make_it_rain<CR>")

vim.keymap.set("v", "<leader>r", ":'<,'>norm .<CR>", { desc = "Repeat last normal command on selection" })
