" Plugin management
set nocompatible
filetype off

" Required:
set runtimepath+=/home/user/.config/nvim/dein/repos/github.com/Shougo/dein.vim
set runtimepath^=/home/user/.config/nvim/dein/repos/github.com/kien/ctrlp.vim

" Required:
if dein#load_state('/home/user/.config/nvim/dein')
    call dein#begin('/home/user/.config/nvim/dein')

    " Let dein manage dein
    " Required:
    call dein#add('/home/user/.config/nvim/dein/repos/github.com/Shougo/dein.vim')

    " lazy load on insert mode
    "call dein#add('Shougo/deoplete.nvim',  {'on_i': 1})
    call dein#add('Shougo/deoplete.nvim')
    call dein#add('zchee/deoplete-jedi')
    " Use deoplete.
    call dein#add('kien/ctrlp.vim')
    " Add or remove your plugins here:
"    call dein#add('Shougo/neosnippet.vim')
"    call dein#add('Shougo/neosnippet-snippets')

    call dein#add('tpope/vim-fugitive')

    " You can specify revision/branch/tag.
    " call dein#add('Shougo/vimshell', { 'rev': '3787e5' })

    " Required:
    call dein#end()
    call dein#save_state()
endif

" Required:
filetype plugin indent on
syntax enable

" If you want to install not installed plugins on startup.
"if dein#check_install()
"  call dein#install()
"endif


" Disabled vundle for now, testing dein
"set rtp+=~/.config/nvim/bundle/Vundle.vim
"call vundle#begin('~/.config/nvim/bundle')
"
"Plugin 'VundleVim/Vundle.vim'
"
"" Custom plugins...
"" Plugin 'Valloric/YouCompleteMe'
"
"" After all plugins...
"call vundle#end()
"filetype plugin indent on




""""""" General coding stuff """""""
" Highlight 80th column
" set colorcolumn=80
" Always show status bar
    call dein#add('zchee/deoplete-jedi')
set laststatus=2
" Let plugins show effects after 500ms, not 4s
set updatetime=500
" Disable mouse click to go to position
" set mouse-=a
" Don't let autocomplete affect usual typing habits
"set completeopt=menuone,preview,noinsert
" Let vim-gitgutter do its thing on large files
"let g:gitgutter_max_signs=10000

" If your terminal's background is white (light theme), uncomment the following
" to make EasyMotion's cues much easier to read.
" hi link EasyMotionTarget String
" hi link EasyMotionShade Comment
" hi link EasyMotionTarget2First String
" hi link EasyMotionTarget2Second Statement


""""""" Python stuff """""""
syntax enable
set relativenumber showmatch
set number
"set shiftwidth=4 tabstop=4 softtabstop=4 expandtab autoindent
let python_highlight_all = 1


""""""" Keybindings """""""
" Set up leaders
"let mapleader=","
"let maplocalleader="\\"

" Mac OS X option-left / right
"noremap â b
"noremap æ e
"inoremap â <C-o>b
"inoremap æ <C-o>e<right>
" Note - this required binding in preferences (Cmd-,) option+backspace to
" escape+z.
" Why this one is complicated - <C-o> at end of line moves cursor by one
" character, which means a trailing character could be left.
" inoremap <expr> ú col('.')>1 ? 'T<Left><C-o>db<Delete>' : '<Backspace>T<Left><c-o>db<Delete>'
" Requires binding option+forward delete to escape
 "inoremap ø <C-o>dw

" Linux / windows ctrl+backspace ctrl+delete
" Note that ctrl+backspace doesn't work in Linux, so ctrl+\ is also available
" imap <C-backspace> ú
" imap <C-\> ú
" imap <C-delete> ø

" Arrow keys up/down move visually up and down rather than by whole lines.  In
" other words, wrapped lines will take longer to scroll through, but better
" control in long bodies of text.
" NOTE - Disabled since <leader><leader>w|e|b works well with easymotion
"noremap <up> gk
"noremap <down> gj

" Neomake and other build commands (ctrl-b)
" nnoremap <C-b> :w<cr>:Neomake<cr>
" autocmd BufNewFile,BufRead *.tex,*.bib noremap <buffer> <C-b> :w<cr>:new<bar>r !make<cr>:setlocal buftype=nofile<cr>:setlocal bufhidden=hide<cr>:setlocal noswapfile<cr>
" autocmd BufNewFile,BufRead *.tex,*.bib imap <buffer> <C-b> <Esc><C-b><Paste>


" allow backspacing over everything in insert mode
set backspace=indent,eol,start

if has("vms")
  set nobackup      " do not keep a backup file, use versions instead
else
  set backup        " keep a backup file (restore to previous version)
  set undofile      " keep an undo file (undo changes after closing)
endif
set history=50      " keep 50 lines of command line history
set ruler       " show the cursor position all the time
set showcmd     " display incomplete commands
set incsearch       " do incremental searching

" For Win32 GUI: remove 't' flag from 'guioptions': no tearoff menu entries
" let &guioptions = substitute(&guioptions, "t", "", "g")

" Don't use Ex mode, use Q for formatting
map Q gq

" CTRL-U in insert mode deletes a lot.  Use CTRL-G u to first break undo,
" so that you can undo CTRL-U after inserting a line break.
inoremap <C-U> <C-G>u<C-U>

" In many terminal emulators the mouse works just fine, thus enable it.
if has('mouse')
  set mouse=a
endif

" Switch syntax highlighting on, when the terminal has colors
" Also switch on highlighting the last used search pattern.
if &t_Co > 2 || has("gui_running")
  syntax on
  set hlsearch
endif

" Only do this part when compiled with support for autocommands.
if has("autocmd")

  " Enable file type detection.
  " Use the default filetype settings, so that mail gets 'tw' set to 72,
  " 'cindent' is on in C files, etc.
  " Also load indent files, to automatically do language-dependent indenting.
  filetype plugin indent on

  " Put these in an autocmd group, so that we can delete them easily.
  augroup vimrcEx
  au!

  " When editing a file, always jump to the last known cursor position.
  " Don't do it when the position is invalid or when inside an event handler
  " (happens when dropping a file on gvim).
  " Also don't do it when the mark is in the first line, that is the default
  " position when opening a file.
  autocmd BufReadPost *
    \ if line("'\"") > 1 && line("'\"") <= line("$") |
    \   exe "normal! g`\"" |
    \ endif

  augroup END

else

  set autoindent        " always set autoindenting on

endif " has("autocmd")

" Convenient command to see the difference between the current buffer and the
" file it was loaded from, thus the changes you made.
" Only define it when not defined already.
if !exists(":DiffOrig")
  command DiffOrig vert new | set bt=nofile | r ++edit # | 0d_ | diffthis
          \ | wincmd p | diffthis
endif

" Default filetype is plugin
filetype plugin indent on
" Indenting the next lines in a scope by 4 spaces
set shiftwidth=4
" Replacing shift with tabs
set expandtab
" Dont know what this do yet, 
"set backspace=2,indent,eol,start
" Tab is 4 spaces
set tabstop=4
" Color mode is adjusted for dark background
set background=dark
" Syntax highlight
syntax on
"Allow saving of files as sudo when I forgot to start vim using sudo."
cmap w!! w !sudo tee > /dev/null %

" XML Lint
map @@x !%xmllint --format --recover -^M

" Setting special chars"
set list
set listchars=tab:→\ ,trail:·,extends:>,precedes:<

" Setting visual mode colors"
hi Visual term=reverse cterm=reverse guibg=Grey

" Highlight search"
set hlsearch

" Case insensitive search
set ignorecase


" Setting python, suppose to make startup faster
let g:python_host_prog  = '/usr/bin/python'
let g:python3_host_prog = '/usr/bin/python3'
"let g:loaded_python_provider = 1
"let g:loaded_python3_provider = 1
"let g:python_host_skip_check = 1
"let g:python3_host_skip_check = 1

" removing trailing white spaces
autocmd BufWritePre *.py :%s/\s\+$//e

let g:deoplete#enable_at_startup = 1
if !exists('g:deoplete#omni#input_patterns')
  let g:deoplete#omni#input_patterns = {}
endif
" let g:deoplete#disable_auto_complete = 1
autocmd InsertLeave,CompleteDone * if pumvisible() == 0 | pclose | endif


" ctlp settings
let g:ctrlp_map = '<c-p>'
let g:ctrlp_cmd = 'CtrlPMixed'


let g:ctrlp_extensions = ['tag', 'buffertag', 'quickfix', 'dir', 'rtscript',
                          \ 'undo', 'line', 'changes', 'mixed', 'bookmarkdir']


" Count occurances of current word in file with *
map ,* *<C-O>:%s///gn<CR>

" Search and replace current word in curor, <Leader>s
nnoremap <Leader>s :%s/\<<C-r><C-w>\>//g<Left><Left>

" Trying to escape modes faster
set timeoutlen=1000 ttimeoutlen=0

"map up/down arrow keys to unimpaired commands
nmap <Up> [e
nmap <Down> ]e
vmap <Up> [egv
vmap <Down> ]egv

"map left/right arrow keys to indendation
nmap <Left> <<
nmap <Right> >>
vmap <Left> <gv
vmap <Right> >gv

" I think this is un-highlighting search with \/
noremap <Leader>/ :nohls<CR>

" noremap <C-j> <C-w>j
" noremap <C-k> <C-w>k
" noremap <C-l> <C-w>l
" noremap <C-h> <C-w>h

" Exiting insert mode with jk
inoremap jk <Esc><Esc>

" Hard mode - Setting escape not to work in insert mode,
inoremap <esc> <nop>
inoremap <Left> <nop>
inoremap <Right> <nop>
inoremap <Up> <nop>
inoremap <Down> <nop>

