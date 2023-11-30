return {
  {
    "ThePrimeagen/harpoon",
    -- set marks specific to each git branch inside git repository
    -- mark_branch = true,

    -- "tg0h/harpoon",
    -- branch = "feat/base-dirs",
    config = function()
      require("telescope").load_extension("harpoon")

      -- Harpoon keymaps
      local mark = require("harpoon.mark")
      local ui = require("harpoon.ui")

      vim.keymap.set("n", "<leader>a", mark.add_file, { desc = "Harpoon - add file" })
      vim.keymap.set("n", "<C-e>", ui.toggle_quick_menu, { desc = "Harpoon - toggle menu" })

      vim.keymap.set("n", "<C-h>", function()
        ui.nav_file(1)
      end, { desc = "Harpoon - Go to 1st file" })
      vim.keymap.set("n", "<C-t>", function()
        ui.nav_file(2)
      end, { desc = "Harpoon - Go to 2nd file" })
      vim.keymap.set("n", "<C-n>", function()
        ui.nav_file(3)
      end, { desc = "Harpoon - Go to 3rd file" })
      vim.keymap.set("n", "<C-s>", function()
        ui.nav_file(4)
      end, { desc = "Harpoon - Go to 4th file" })
    end,
  },
}
