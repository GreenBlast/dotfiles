return {
  {
    "ThePrimeagen/harpoon",
    branch = "harpoon2",
    dependencies = { "nvim-lua/plenary.nvim" },

    -- set marks specific to each git branch inside git repository
    -- mark_branch = true,

    -- "tg0h/harpoon",
    -- branch = "feat/base-dirs",
    config = function()
      local harpoon = require("harpoon")

      -- REQUIRED
      harpoon:setup({})
      -- REQUIRED

      -- require("telescope").load_extension("harpoon")

      -- Harpoon keymaps
      -- local mark = require("harpoon.mark")
      -- local ui = require("harpoon.ui")
      --
      -- vim.keymap.set("n", "<leader>a", mark.add_file, { desc = "Harpoon - add file" })
      -- vim.keymap.set("n", "<C-e>", ui.toggle_quick_menu, { desc = "Harpoon - toggle menu" })
      --
      -- vim.keymap.set("n", "<C-h>", function()
      --   ui.nav_file(1)
      -- end, { desc = "Harpoon - Go to 1st file" })
      -- vim.keymap.set("n", "<C-j>", function()
      --   ui.nav_file(2)
      -- end, { desc = "Harpoon - Go to 2nd file" })
      -- vim.keymap.set("n", "<C-k>", function()
      --   ui.nav_file(3)
      -- end, { desc = "Harpoon - Go to 3rd file" })
      -- vim.keymap.set("n", "<C-l>", function()
      --   ui.nav_file(4)
      -- end, { desc = "Harpoon - Go to 4th file" })

      vim.keymap.set("n", "<leader>a", function()
        harpoon:list():append()
      end)
      vim.keymap.set("n", "<C-e>", function()
        harpoon.ui:toggle_quick_menu(harpoon:list())
      end)

      vim.keymap.set("n", "<C-h>", function()
        harpoon:list():select(1)
      end)
      vim.keymap.set("n", "<C-j>", function()
        harpoon:list():select(2)
      end)
      vim.keymap.set("n", "<C-k>", function()
        harpoon:list():select(3)
      end)
      vim.keymap.set("n", "<C-l>", function()
        harpoon:list():select(4)
      end)

      -- Toggle previous & next buffers stored within Harpoon list
      vim.keymap.set("n", "<C-S-P>", function()
        harpoon:list():prev()
      end)
      vim.keymap.set("n", "<C-S-N>", function()
        harpoon:list():next()
      end)

      local conf = require("telescope.config").values
      local function toggle_telescope(harpoon_files)
        local file_paths = {}
        for _, item in ipairs(harpoon_files.items) do
          table.insert(file_paths, item.value)
        end

        require("telescope.pickers")
          .new({}, {
            prompt_title = "Harpoon",
            finder = require("telescope.finders").new_table({
              results = file_paths,
            }),
            previewer = conf.file_previewer({}),
            sorter = conf.generic_sorter({}),
          })
          :find()
      end

      vim.keymap.set("n", "<C-e>", function()
        toggle_telescope(harpoon:list())
      end, { desc = "Open harpoon window" })
    end,
  },
}
