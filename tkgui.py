#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pylint:disable=unused-wildcard-import,wildcard-import,too-many-lines
"""TKinter-based GUI for PyLNP."""
from __future__ import print_function, unicode_literals

import os
import sys
import errorlog

if sys.version_info[0] == 3:  # Alternate import names
    # pylint:disable=import-error
    from tkinter import *
    from tkinter.ttk import *
    import tkinter.messagebox as messagebox
    import tkinter.simpledialog as simpledialog
else:
    # pylint:disable=import-error
    from Tkinter import *
    from ttk import *
    import tkMessageBox as messagebox
    import tkSimpleDialog as simpledialog

# Workaround to use Pillow in PyInstaller
import pkg_resources  # pylint:disable=unused-import

try:  # PIL-compatible library (e.g. Pillow); used to load PNG images (optional)
    # pylint:disable=import-error,no-name-in-module
    from PIL import Image, ImageTk
    has_PIL = True
except ImportError:  # Some PIL installations live outside of the PIL package
    # pylint:disable=import-error,no-name-in-module
    try:
        import Image
        import ImageTk
        has_PIL = True
    except ImportError:  # No PIL compatible library
        has_PIL = False

force_PNG = (TkVersion >= 8.6)  # Tk 8.6 supports PNG natively

if not (has_PIL or force_PNG):
    print(
        'Note: PIL not found and Tk version too old for PNG support ({0}).'
        'Falling back to GIF images.'.format(TkVersion), file=sys.stderr)


def get_image(filename):
    """
    Open the image with the appropriate extension.

    Params:
        filename
            The base name of the image file.

    Returns:
        A PhotoImage object ready to use with Tkinter.
    """
    if has_PIL or force_PNG:
        filename = filename + '.png'
    else:
        filename = filename + '.gif'
    if has_PIL:
        # pylint:disable=maybe-no-member
        return ImageTk.PhotoImage(Image.open(filename))
    else:
        return PhotoImage(file=filename)


# Make Enter on button with focus activate it
TtkButton = Button
class Button(TtkButton):  # pylint:disable=function-redefined,missing-docstring
    def __init__(self, master=None, **kw):
        TtkButton.__init__(self, master, **kw)
        if 'command' in kw:
            self.bind('<Return>', lambda e: kw['command']())

# Monkeypatch simpledialog to use themed dialogs from ttk
if sys.platform != 'darwin':  # OS X looks better without patch
    simpledialog.Toplevel = Toplevel
    simpledialog.Entry = Entry
    simpledialog.Frame = Frame
    simpledialog.Button = Button


def validate_number(value_if_allowed):
    """
    Validation method used by Tkinter. Accepts empty and float-coercable
    strings.

    Params:
        value_if_allowed
            Value to validate.

    Returns:
        True if value_if_allowed is empty, or can be interpreted as a float.
    """
    if value_if_allowed == '':
        return True
    try:
        float(value_if_allowed)
        return True
    except ValueError:
        return False


# http://www.voidspace.org.uk/python/weblog/arch_d7_2006_07_01.shtml#e387
class ToolTip(object):
    """Tooltip widget."""
    def __init__(self, widget, text):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.event = None
        self.x = self.y = 0
        self.text = text
        self.active = False

    def showtip(self):
        """Displays the tooltip."""
        self.active = True
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_pointerx() + 16
        y = self.widget.winfo_pointery() + 16
        self.tipwindow = tw = Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        try:
            # For OS X
            tw.tk.call(
                "::tk::unsupported::MacWindowStyle", "style", tw._w, "help",
                "noActivates")
        except TclError:
            pass
        label = Label(
            tw, text=self.text, justify=LEFT, background="#ffffe0",
            relief=SOLID, borderwidth=1)
        label.pack(ipadx=1)

    def hidetip(self):
        """Hides the tooltip."""
        tw = self.tipwindow
        self.tipwindow = None
        self.active = False
        if tw:
            tw.destroy()

    def settext(self, text):
        """
        Sets the tooltip text and redraws it if necessary.

        Params:
            text
                The new tooltip text.
        """
        if text == self.text:
            return
        self.text = text
        if self.active:
            self.hidetip()
            self.showtip()

_TOOLTIP_DELAY = 500


def create_tooltip(widget, text):
    """
    Creates and returns a tooltip for a widget.

    Params:
        widget
            The widget to associate the tooltip to.
        text
            The tooltip text.
    """
    # pylint:disable=unused-argument
    tooltip = ToolTip(widget, text)

    def enter(event):
        """
        Event handler on mouse enter.

        Params:
            event
                The event data."""
        if tooltip.event:
            widget.after_cancel(tooltip.event)
        tooltip.event = widget.after(_TOOLTIP_DELAY, tooltip.showtip)

    def leave(event):
        """
        Event handler on mouse exit.

        Params:
            event
                The event data.
        """
        if tooltip.event is not None:
            widget.after_cancel(tooltip.event)
            tooltip.event = None
        tooltip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)
    return tooltip

class LogWindow(object):
    """Window used for displaying an error log."""
    def __init__(self, parent):
        """
        Constructor for LogWindow.

        Params:
            parent
                Parent widget for the window.
        """
        top = self.top = Toplevel(parent)
        top.title('Output log')

        f = Frame(top)
        Button(f, text='Refresh', command=self.load).pack(side=LEFT)
        f.pack(side=TOP, anchor='w')

        f = Frame(top)
        Grid.rowconfigure(f, 0, weight=1)
        Grid.columnconfigure(f, 0, weight=1)
        Grid.columnconfigure(f, 2, weight=1)
        self.out = Text(f, width=40, height=20, wrap="word")
        self.out.grid(column=0, row=0, sticky="nsew")
        s = Scrollbar(f, orient=VERTICAL, command=self.out.yview)
        self.out['yscrollcommand'] = s.set
        s.grid(column=1, row=0, sticky="ns")
        self.err = Text(f, width=40, height=20, wrap="word")
        self.err.grid(column=2, row=0, sticky="nsew")
        s = Scrollbar(f, orient=VERTICAL, command=self.err.yview)
        self.err['yscrollcommand'] = s.set
        s.grid(column=3, row=0, sticky="ns")
        f.pack(side=BOTTOM, fill=BOTH, expand=Y)
        self.load()

    def load(self):
        """Loads log data into the text widgets."""
        self.out.delete('1.0', END)
        self.err.delete('1.0', END)
        self.out.insert('1.0', '\n'.join(errorlog.out.lines))
        self.err.insert('1.0', '\n'.join(errorlog.err.lines))


class InitEditor(object):
    """Basic editor for d_init.txt and init.txt."""
    def __init__(self, parent, gui):
        """
        Constructor for InitEditor.

        Params:
            parent
                Parent widget for the window.
            gui
                Parent TkGui instance for communication.
        """
        self.gui = gui
        top = self.top = Toplevel(parent)
        top.title('Init Editor')

        f = Frame(top)
        b = Button(f, text="Load", command=self.load)
        b.pack(side=LEFT)
        b = Button(f, text="Save", command=self.save)
        b.pack(side=LEFT)
        f.pack(side=TOP, anchor="w")

        f = Frame(top)
        Grid.rowconfigure(f, 0, weight=1)
        Grid.columnconfigure(f, 0, weight=1)
        Grid.columnconfigure(f, 2, weight=1)
        self.init_text = Text(f, width=40, height=20, wrap="word")
        self.init_text.grid(column=0, row=0, sticky="nsew")
        s = Scrollbar(f, orient=VERTICAL, command=self.init_text.yview)
        self.init_text['yscrollcommand'] = s.set
        s.grid(column=1, row=0, sticky="ns")
        self.d_init_text = Text(f, width=40, height=20, wrap="word")
        self.d_init_text.grid(column=2, row=0, sticky="nsew")
        s = Scrollbar(f, orient=VERTICAL, command=self.d_init_text.yview)
        self.d_init_text['yscrollcommand'] = s.set
        s.grid(column=3, row=0, sticky="ns")
        f.pack(side=BOTTOM, fill=BOTH, expand=Y)
        self.load()

    def load(self):
        """Loads configuration data into the text widgets."""
        self.gui.save_params()
        self.init_text.delete('1.0', END)
        self.init_text.insert('1.0', open(
            os.path.join(self.gui.lnp.init_dir, 'init.txt')).read())
        self.d_init_text.delete('1.0', END)
        self.d_init_text.insert('1.0', open(
            os.path.join(self.gui.lnp.init_dir, 'd_init.txt')).read())

    def save(self):
        """Saves configuration data from the text widgets."""
        f = open(os.path.join(self.gui.lnp.init_dir, 'init.txt'), 'w')
        f.write(self.init_text.get('1.0', 'end'))
        f.close()
        f = open(os.path.join(self.gui.lnp.init_dir, 'd_init.txt'), 'w')
        f.write(self.d_init_text.get('1.0', 'end'))
        f.close()
        self.gui.load_params()


class SelectDF(object):
    """Window to select an instance of Dwarf Fortress to operate on."""
    def __init__(self, parent, folders):
        """
        Constructor for SelectDF.

        Params:
            parent
                Parent widget for the window.
            folders
                List of suitable folder paths.
        """
        self.parent = parent
        top = self.top = Toplevel(parent)
        top.title('Select DF instance')

        self.result = ''

        self.listvar = Variable(top)
        self.listvar.set(folders)

        f = Frame(top)
        Grid.rowconfigure(f, 1, weight=1)
        Grid.columnconfigure(f, 0, weight=1)
        Label(
            f, text='Please select the Dwarf Fortress folder '
            'you would like to use.').grid(column=0, row=0, columnspan=2)
        self.folderlist = Listbox(
            f, listvariable=self.listvar, activestyle='dotbox')
        self.folderlist.grid(column=0, row=1, sticky="nsew")
        s = Scrollbar(f, orient=VERTICAL, command=self.folderlist.yview)
        self.folderlist['yscrollcommand'] = s.set
        s.grid(column=1, row=1, sticky="ns")
        Button(
            f, text='OK', command=self.ok
            ).grid(column=0, row=2, columnspan=2, sticky="s")
        self.folderlist.bind("<Double-1>", lambda e: self.ok())
        f.pack(fill=BOTH, expand=Y)

        top.transient(parent)
        top.wait_visibility()
        top.grab_set()
        top.focus_set()
        top.protocol("WM_DELETE_WINDOW", self.cancel)
        top.wait_window(top)

    def ok(self):
        """Called when the OK button is clicked."""
        if len(self.folderlist.curselection()) != 0:
            self.result = self.folderlist.get(self.folderlist.curselection()[0])
            self.top.protocol('WM_DELETE_WINDOW', None)
            self.top.destroy()

    def cancel(self):
        """Called when the Cancel button is clicked."""
        self.top.destroy()


class UpdateWindow(object):
    """Notification of a new update."""
    def __init__(self, parent, lnp):
        """
        Constructor for UpdateWindow.

        Params:
            parent
                Parent widget for the window.
            lnp
                Reference to the PyLNP object.
        """
        self.parent = parent
        self.lnp = lnp
        top = self.top = Toplevel(parent)
        top.title('Select DF instance')

        f = Frame(top)
        Grid.rowconfigure(f, 1, weight=1)
        Grid.columnconfigure(f, 0, weight=1)
        Label(
            f, text='Update is available (version '+self.lnp.new_version +
            '). Update now?').grid(column=0, row=0, columnspan=2)
        Label(f, text='Check again in').grid(column=0, row=1)

        self.options = [
            "next launch", "1 day", "3 days", "7 days", "14 days", "30 days"]
        self.var = StringVar(top)
        try:
            default_idx = [0, 1, 3, 7, 14, 30].index(
                self.lnp.userconfig.get_number('updateDays'))
        except ValueError:
            default_idx = 0
        self.var.set(self.options[default_idx])
        OptionMenu(f, self.var, self.options[default_idx], *self.options).grid(
            column=1, row=1)
        f.pack(fill=BOTH, expand=Y)

        buttons = Frame(top)
        Button(
            buttons, text='Yes', command=self.yes
            ).pack(side=LEFT)
        Button(
            buttons, text='No', command=self.close
            ).pack(side=LEFT)
        buttons.pack(side=BOTTOM, anchor="e")

        top.transient(parent)
        top.wait_visibility()
        top.grab_set()
        top.focus_set()
        top.protocol("WM_DELETE_WINDOW", self.close)
        top.wait_window(top)

    def yes(self):
        """Called when the Yes button is clicked."""
        self.lnp.start_update()
        self.close()

    def close(self):
        """Called when the window is closed."""
        days = [0, 1, 3, 7, 14, 30][self.options.index(self.var.get())]
        self.lnp.next_update(days)
        self.top.destroy()


class TkGui(object):
    """Main GUI window."""
    def __init__(self, lnp):
        """
        Constructor for TkGui.

        Params:
            lnp
                A PyLNP instance to perform actual work.
        """
        self.lnp = lnp
        self.root = root = Tk()

        root.option_add('*tearOff', FALSE)
        windowing = root.tk.call('tk', 'windowingsystem')
        if windowing == "win32":
            if self.lnp.bundle == "win":
                # pylint: disable=protected-access, no-member
                img = os.path.join(sys._MEIPASS, 'LNP.ico')
            else:
                img = 'LNP.ico'
            root.tk.call('wm', 'iconbitmap', root, "-default", img)
        elif windowing == "x11":
            if self.lnp.bundle == 'linux':
                # pylint: disable=protected-access, no-member
                img = get_image(os.path.join(sys._MEIPASS, 'LNP'))
            else:
                img = get_image('LNP')
            root.tk.call('wm', 'iconphoto', root, "-default", img)
        elif windowing == "aqua":  # OS X has no window icons
            pass

        root.resizable(0, 0)
        root.title("PyLNP")
        self.vcmd = (root.register(validate_number), '%P')
        self.keybinds = Variable(root)
        self.graphics = Variable(root)
        self.progs = Variable(root)
        self.colors = Variable(root)
        self.embarks = Variable(root)

        self.volume_var = StringVar()
        self.fps_var = StringVar()
        self.gps_var = StringVar()

        self.controls = dict()
        self.proglist = None
        self.color_files = None
        self.color_preview = None
        self.hacklist = None
        self.hack_tooltip = None

        main = Frame(root)
        if self.lnp.bundle == 'osx':
            # Image is inside application bundle on OS X
            image = os.path.join(
                os.path.dirname(sys.executable), '..', 'Resources', 'LNPSMALL')
        elif self.lnp.bundle in ['win', 'linux']:
            # Image is inside executable on Linux and Windows
            # pylint: disable=protected-access, no-member
            image = os.path.join(sys._MEIPASS, 'LNPSMALL')
        else:
            image = 'LNPSMALL'
        logo = get_image(image)
        Label(root, image=logo).pack()
        main.pack(side=TOP, fill=BOTH, expand=Y)
        n = Notebook(main)
        f1 = self.create_options(n)
        f2 = self.create_graphics(n)
        f3 = self.create_utilities(n)
        f4 = self.create_advanced(n)
        n.add(f1, text='Options')
        n.add(f2, text='Graphics')
        n.add(f3, text='Utilities')
        n.add(f4, text='Advanced')
        if self.lnp.config.get_list('dfhack'):
            f5 = self.create_dfhack(n)
            n.add(f5, text='DFHack')
        n.enable_traversal()
        n.pack(fill=BOTH, expand=Y, padx=2, pady=3)

        main_buttons = Frame(main)
        main_buttons.pack(side=BOTTOM)

        play = Button(
            main_buttons, text='Play Dwarf Fortress!', command=self.lnp.run_df)
        create_tooltip(play, 'Play the game!')
        init = Button(main_buttons, text='Init Editor', command=self.run_init)
        create_tooltip(init, 'Edit init and d_init in a built-in text editor')
        defaults = Button(
            main_buttons, text='Defaults', command=self.restore_defaults)
        create_tooltip(defaults, 'Reset everything to default settings')
        play.grid(column=0, row=0, sticky="nsew")
        init.grid(column=1, row=0, sticky="nsew")
        defaults.grid(column=2, row=0, sticky="nsew")

        self.create_menu(root)

        if lnp.df_dir == '':
            if lnp.folders:
                selector = SelectDF(self.root, lnp.folders)
                if selector.result == '':
                    messagebox.showerror(
                        self.root.title(),
                        'No Dwarf Fortress install was selected, quitting.')
                    self.root.destroy()
                    return
                else:
                    try:
                        lnp.set_df_folder(selector.result)
                    except IOError as e:
                        messagebox.showerror(self.root.title(), e.message)
                        self.exit_program()
                        return
            else:
                messagebox.showerror(
                    self.root.title(),
                    "Could not find Dwarf Fortress, quitting.")
                self.root.destroy()
                return

        self.read_keybinds()
        self.read_graphics()
        self.read_utilities()
        self.update_displays()
        self.read_colors()
        self.read_embarks()
        if self.lnp.config.get_list('dfhack'):
            self.update_hack_list()

        if self.lnp.new_version is not None:
            UpdateWindow(self.root, self.lnp)

        root.mainloop()

    def create_options(self, n):
        """
        Creates the Options tab.

        Params:
            n
                Notebook instance to create the tab in.
        """
        f = Frame(n)
        f.pack(side=TOP, fill=BOTH, expand=Y)
        options = Labelframe(f, text='Options')
        options.pack(side=TOP, fill=BOTH, expand=N)
        Grid.columnconfigure(options, 0, weight=1)
        Grid.columnconfigure(options, 1, weight=1)

        population = Button(
            options, text='Population Cap', command=self.set_pop_cap)
        create_tooltip(population, 'Maximum population in your fort')
        population.grid(column=0, row=0, sticky="nsew")
        self.controls['popcap'] = population
        invaders = Button(
            options, text='Invaders',
            command=lambda: self.cycle_option('invaders'))
        create_tooltip(
            invaders, 'Toggles whether invaders (goblins, etc.) show up')
        invaders.grid(column=1, row=0, sticky="nsew")
        self.controls['invaders'] = invaders
        childcap = Button(
            options, text='Child Cap', command=self.set_child_cap)
        create_tooltip(childcap, 'Maximum children in your fort')
        childcap.grid(column=0, row=1, sticky="nsew")
        self.controls['childcap'] = childcap
        caveins = Button(
            options, text='Cave-ins',
            command=lambda: self.cycle_option('caveins'))
        create_tooltip(
            caveins,
            'Toggles whether unsupported bits of terrain will collapse')
        caveins.grid(column=1, row=1, sticky="nsew")
        self.controls['caveins'] = caveins
        temperature = Button(
            options, text='Temperature',
            command=lambda: self.cycle_option('temperature'))
        create_tooltip(
            temperature,
            'Toggles whether things will burn, melt, freeze, etc.')
        temperature.grid(column=0, row=2, sticky="nsew")
        self.controls['temperature'] = temperature
        liquid_depth = Button(
            options, text='Liquid Depth',
            command=lambda: self.cycle_option('liquidDepth'))
        create_tooltip(
            liquid_depth,
            'Displays the depth of liquids with numbers 1-7')
        liquid_depth.grid(column=1, row=2, sticky="nsew")
        self.controls['liquidDepth'] = liquid_depth
        weather = Button(
            options, text='Weather',
            command=lambda: self.cycle_option('weather'))
        create_tooltip(weather, 'Rain, snow, etc.')
        weather.grid(column=0, row=3, sticky="nsew")
        self.controls['weather'] = weather
        varied_ground = Button(
            options, text='Varied Ground',
            command=lambda: self.cycle_option('variedGround'))
        create_tooltip(
            varied_ground,
            'If ground tiles use a variety of punctuation, or only periods')
        varied_ground.grid(column=1, row=3, sticky="nsew")
        self.controls['variedGround'] = varied_ground
        starting_labors = Button(
            options, text='Starting Labors',
            command=lambda: self.cycle_option('laborLists'))
        create_tooltip(
            starting_labors, 'Which labors are enabled by default:'
            'by skill level of dwarves, by their unit type, or none')
        starting_labors.grid(column=0, row=4, columnspan=2, sticky="nsew")
        self.controls['laborLists'] = starting_labors

        modifications = Labelframe(f, text='Modifications', width=192)
        modifications.pack(side=TOP, expand=N, anchor="w")
        Grid.columnconfigure(modifications, 0, weight=1)
        Grid.columnconfigure(modifications, 1, weight=1)

        aquifers = Button(
            modifications, text='Aquifers',
            command=lambda: self.cycle_option('aquifers'))
        create_tooltip(
            aquifers, 'Whether newly created worlds will have Aquifers in them '
            '(Infinite sources of underground water, but may flood your fort')
        aquifers.grid(column=0, row=0, sticky="nsew")
        self.controls['aquifers'] = aquifers

        keybindings = Labelframe(f, text='Key Bindings')
        keybindings.pack(
            side=BOTTOM, fill=BOTH, expand=Y)
        Grid.columnconfigure(keybindings, 0, weight=2)
        Grid.rowconfigure(keybindings, 1, weight=1)

        keybinding_files = Listbox(
            keybindings, height=4, listvariable=self.keybinds,
            activestyle='dotbox')
        keybinding_files.grid(column=0, row=0, rowspan=2, sticky="nsew")
        s = Scrollbar(
            keybindings, orient=VERTICAL, command=keybinding_files.yview)
        keybinding_files['yscrollcommand'] = s.set
        s.grid(column=1, row=0, rowspan=2, sticky="ns")

        buttons = Frame(keybindings)
        load_keyb = Button(
            buttons, text='Load',
            command=lambda: self.load_keybinds(keybinding_files))
        load_keyb.pack(side=TOP)
        create_tooltip(load_keyb, 'Load selected keybindings')
        refresh_keyb = Button(
            buttons, text='Refresh', command=self.read_keybinds)
        create_tooltip(refresh_keyb, 'Refresh keybinding list')
        refresh_keyb.pack(side=TOP)
        save_keyb = Button(buttons, text='Save', command=self.save_keybinds)
        create_tooltip(save_keyb, 'Save your current keybindings')
        save_keyb.pack(side=TOP)
        delete_keyb = Button(
            buttons, text='Delete',
            command=lambda: self.delete_keybinds(keybinding_files))
        create_tooltip(delete_keyb, 'Delete selected keybinding')
        delete_keyb.pack(side=TOP)
        buttons.grid(column=2, row=0)

        embarks = Labelframe(f, text='Embark profiles')
        embarks.pack(
            side=BOTTOM, fill=BOTH, expand=Y)
        Grid.columnconfigure(embarks, 0, weight=2)
        Grid.rowconfigure(embarks, 1, weight=1)

        embark_files = Listbox(
            embarks, height=4, listvariable=self.embarks,
            activestyle='dotbox', selectmode='multiple')
        embark_files.grid(column=0, row=0, rowspan=2, sticky="nsew")
        s = Scrollbar(
            embarks, orient=VERTICAL, command=embark_files.yview)
        embark_files['yscrollcommand'] = s.set
        s.grid(column=1, row=0, rowspan=2, sticky="ns")

        buttons = Frame(embarks)
        install_embarks = Button(
            buttons, text='Load',
            command=lambda: self.install_embarks(embark_files))
        install_embarks.pack(side=TOP)
        create_tooltip(install_embarks, 'Load selected embark profiles')
        refresh_embarks = Button(
            buttons, text='Refresh', command=self.read_embarks)
        create_tooltip(refresh_embarks, 'Refresh embark profile list')
        refresh_embarks.pack(side=TOP)
        buttons.grid(column=2, row=0)

        return f

    def create_graphics(self, n):
        """
        Creates the Graphics tab.

        Params:
            n
                Notebook instance to create the tab in.
        """
        f = Frame(n)
        f.pack(side=TOP, fill=BOTH, expand=Y)

        change_graphics = Labelframe(f, text='Change Graphics')
        change_graphics.pack(side=TOP, fill=BOTH, expand=Y)
        Grid.columnconfigure(change_graphics, 0, weight=1)
        Grid.columnconfigure(change_graphics, 1, weight=1)

        curr_pack = Label(change_graphics, text='Current Graphics')
        curr_pack.grid(column=0, row=0, columnspan=2, sticky="nsew")
        self.controls['FONT'] = (curr_pack, lambda x: self.lnp.current_pack())

        graphicpacks = Listbox(
            change_graphics, height=8, listvariable=self.graphics,
            activestyle='dotbox')
        graphicpacks.grid(column=0, row=1, columnspan=2, sticky="nsew", pady=4)

        install = Button(
            change_graphics, text='Install Graphics',
            command=lambda: self.install_graphics(graphicpacks))
        create_tooltip(install, 'Install selected graphics pack')
        install.grid(column=0, row=2, sticky="nsew")
        update_saves = Button(
            change_graphics, text='Update Savegames',
            command=self.update_savegames)
        create_tooltip(
            update_saves, 'Install current graphics pack in all savegames')
        update_saves.grid(column=1, row=2, sticky="nsew")
        truetype = Button(
            change_graphics, text='TrueType Fonts',
            command=lambda: self.cycle_option('truetype'))
        create_tooltip(
            truetype,
            'Toggles whether to use TrueType fonts or tileset for text')
        truetype.grid(column=0, row=3, columnspan=2, sticky="nsew")
        self.controls['truetype'] = truetype

        advanced = Labelframe(f, text='Advanced')
        advanced.pack(side=BOTTOM, fill=X, expand=Y)
        Grid.columnconfigure(advanced, 0, weight=1)
        Grid.columnconfigure(advanced, 1, weight=1)

        openfolder = Button(
            advanced, text='Open Graphics Folder',
            command=self.lnp.open_graphics)
        openfolder.grid(column=0, row=0, columnspan=2, sticky="nsew")
        create_tooltip(openfolder, 'Add your own graphics packs here!')
        refresh = Button(
            advanced, text='Refresh List', command=self.read_graphics)
        create_tooltip(refresh, 'Refresh list of graphics packs')
        refresh.grid(column=0, row=1, sticky="nsew")
        simplify = Button(
            advanced, text='Simplify Graphic Folders',
            command=self.simplify_graphics)
        create_tooltip(
            simplify, 'Deletes unnecessary files from graphics packs '
            '(saves space, useful for re-packaging)')
        simplify.grid(column=1, row=1, sticky="nsew")

        colors = Labelframe(f, text='Color schemes')
        colors.pack(side=BOTTOM, fill=BOTH, expand=Y, anchor="s")
        Grid.columnconfigure(colors, 0, weight=3)
        Grid.columnconfigure(colors, 2, weight=1)

        self.color_files = color_files = Listbox(
            colors, height=4, listvariable=self.colors,
            activestyle='dotbox')
        color_files.grid(column=0, row=0, rowspan=2, sticky="nsew")
        color_files.bind(
            '<<ListboxSelect>>',
            lambda e: self.paint_color_preview(color_files))
        s = Scrollbar(colors, orient=VERTICAL, command=self.color_files.yview)
        self.color_files['yscrollcommand'] = s.set
        s.grid(column=1, row=0, rowspan=2, sticky="ns")

        buttons = Frame(colors)
        load_color = Button(
            buttons, text='Load',
            command=lambda: self.load_colors(color_files))
        load_color.pack(side=TOP)
        create_tooltip(load_color, 'Load selected color scheme')
        refresh_color = Button(
            buttons, text='Refresh', command=self.read_colors)
        create_tooltip(refresh_color, 'Refresh color scheme list')
        refresh_color.pack(side=TOP)
        save_color = Button(buttons, text='Save', command=self.save_colors)
        create_tooltip(save_color, 'Save your current color scheme')
        save_color.pack(side=TOP)
        delete_color = Button(
            buttons, text='Delete',
            command=lambda: self.delete_colors(color_files))
        create_tooltip(delete_color, 'Delete selected color scheme')
        delete_color.pack(side=TOP)
        buttons.grid(column=2, row=0, rowspan=3)

        self.color_preview = Canvas(
            colors, width=128, height=32, highlightthickness=0, takefocus=False)
        self.color_preview.grid(column=0, row=2)

        return f

    def create_utilities(self, n):
        """
        Creates the Utilities tab.

        Params:
            n
                Notebook instance to create the tab in.
        """
        f = Frame(n)
        f.pack(side=TOP, fill=BOTH, expand=Y)

        progs = Labelframe(f, text='Programs/Utilities')
        progs.pack(side=TOP, expand=Y, fill=BOTH)
        Grid.columnconfigure(progs, 0, weight=1)
        Grid.columnconfigure(progs, 1, weight=1)
        Grid.rowconfigure(progs, 3, weight=1)

        run_prog = Button(
            progs, text='Run Program', command=self.run_selected_utilities)
        create_tooltip(run_prog, 'Runs the selected program(s).')
        run_prog.grid(column=0, row=0, sticky="nsew")
        open_utils = Button(
            progs, text='Open Utilities Folder', command=self.lnp.open_utils)
        create_tooltip(open_utils, 'Open the utilities folder')
        open_utils.grid(column=1, row=0, sticky="nsew")
        Label(
            progs, text='Double-click on a program to launch it.').grid(
                column=0, row=1, columnspan=2)
        Label(
            progs, text='Right-click on a program to toggle auto-launch.').grid(
                column=0, row=2, columnspan=2)
        listframe = Frame(progs)
        listframe.grid(column=0, row=3, columnspan=2, sticky="nsew")
        Grid.rowconfigure(listframe, 0, weight=1)
        Grid.columnconfigure(listframe, 0, weight=1)
        self.proglist = proglist = Treeview(
            listframe, columns=('exe', 'launch'), show=['headings'])
        proglist.column('exe', width=1, anchor='w')
        proglist.column('launch', width=35, anchor='e', stretch=NO)
        proglist.heading('exe', text='Executable')
        proglist.heading('launch', text='Auto')
        proglist.grid(column=0, row=0, sticky="nsew")
        proglist.bind("<Double-1>", lambda e: self.run_selected_utilities())
        if sys.platform == 'darwin':
            proglist.bind("<2>", self.toggle_autorun)
        else:
            proglist.bind("<3>", self.toggle_autorun)
        s = Scrollbar(listframe, orient=VERTICAL, command=proglist.yview)
        proglist['yscrollcommand'] = s.set
        s.grid(column=1, row=0, sticky="ns")

        refresh = Button(
            progs, text='Refresh List', command=self.read_utilities)
        create_tooltip(refresh, 'Refresh the list of utilities')
        refresh.grid(column=0, row=4, columnspan=2, sticky="nsew")
        return f

    def create_advanced(self, n):
        """
        Creates the Advanced tab.

        Params:
            n
                Notebook instance to create the tab in.
        """
        f = Frame(n)
        f.pack(side=TOP, fill=BOTH, expand=Y)
        Grid.columnconfigure(f, 0, weight=1)
        Grid.columnconfigure(f, 1, weight=1)

        sound = Labelframe(f, text='Sound')
        sound.grid(column=0, row=0, sticky="nsew")

        sound_button = Button(
            sound, text='Sound', command=lambda: self.cycle_option('sound'))
        create_tooltip(sound_button, 'Turn game music on/off')
        sound_button.pack(side=LEFT)
        self.controls['sound'] = sound_button
        self.volume_var.trace(
            "w", lambda name, index, mode: self.change_entry(
                'volume', self.volume_var))
        volume = Entry(
            sound, width=4, validate='key', validatecommand=self.vcmd,
            textvariable=self.volume_var)
        create_tooltip(volume, 'Music volume (0 to 255)')
        volume.pack(side=LEFT)
        self.controls['volume'] = volume
        maxvolume = Label(sound, text='/255')
        maxvolume.pack(side=LEFT)

        fps = Labelframe(f, text='FPS')
        fps.grid(column=1, row=0, rowspan=2, sticky="nsew")

        fps_counter = Button(
            fps, text='FPS Counter',
            command=lambda: self.cycle_option('fpsCounter'))
        create_tooltip(fps_counter, 'Whether or not to display your FPS')
        fps_counter.pack(fill=BOTH)
        self.controls['fpsCounter'] = fps_counter
        calc_cap_label = Label(fps, text='Calculation FPS Cap:')
        calc_cap_label.pack(anchor="w")
        self.fps_var.trace(
            "w", lambda name, index, mode: self.change_entry(
                'fpsCap', self.fps_var))
        calc_cap = Entry(
            fps, width=4, validate='key', validatecommand=self.vcmd,
            textvariable=self.fps_var)
        create_tooltip(calc_cap, 'How fast the game runs')
        calc_cap.pack(anchor="w")
        self.controls['fpsCap'] = calc_cap
        graphical_cap_label = Label(fps, text='Graphical FPS Cap:')
        graphical_cap_label.pack(anchor="w")
        self.gps_var.trace(
            "w", lambda name, index, mode: self.change_entry(
                'gpsCap', self.gps_var))
        graphical_cap = Entry(
            fps, width=4, validate='key', validatecommand=self.vcmd,
            textvariable=self.gps_var)
        create_tooltip(
            graphical_cap, 'How fast the game visually updates.\nLower '
            'value may give small boost to FPS but will be less reponsive.')
        graphical_cap.pack(anchor="w")
        self.controls['gpsCap'] = graphical_cap

        startup = Labelframe(f, text='Startup')
        startup.grid(column=0, row=1, sticky="nsew")
        Grid.columnconfigure(startup, 0, weight=1)

        intro = Button(
            startup, text='Intro Movie',
            command=lambda: self.cycle_option('introMovie'))
        create_tooltip(
            intro, 'Do you want to see the beautiful ASCII intro movie?')
        intro.grid(column=0, row=0, sticky="nsew")
        self.controls['introMovie'] = intro
        windowed = Button(
            startup, text='Windowed',
            command=lambda: self.cycle_option('startWindowed'))
        create_tooltip(windowed, 'Start windowed or fullscreen')
        windowed.grid(column=0, row=1, sticky="nsew")
        self.controls['startWindowed'] = windowed

        saverelated = Labelframe(f, text='Save-related')
        saverelated.grid(column=0, row=2, columnspan=2, sticky="nsew")
        Grid.columnconfigure(saverelated, 0, weight=1)
        Grid.columnconfigure(saverelated, 1, weight=1)

        autosave = Button(
            saverelated, text='Autosave',
            command=lambda: self.cycle_option('autoSave'))
        create_tooltip(autosave, 'How often the game will automatically save')
        autosave.grid(column=0, row=0, sticky="nsew")
        self.controls['autoSave'] = autosave
        initialsave = Button(
            saverelated, text='Initial Save',
            command=lambda: self.cycle_option('initialSave'))
        create_tooltip(initialsave, 'Saves as soon as you embark')
        initialsave.grid(column=1, row=0, sticky="nsew")
        self.controls['initialSave'] = initialsave
        pause_save = Button(
            saverelated, text='Pause on Save',
            command=lambda: self.cycle_option('autoSavePause'))
        create_tooltip(pause_save, 'Pauses the game after auto-saving')
        pause_save.grid(column=0, row=1, sticky="nsew")
        self.controls['autoSavePause'] = pause_save
        pause_load = Button(
            saverelated, text='Pause on Load',
            command=lambda: self.cycle_option('pauseOnLoad'))
        create_tooltip(pause_load, 'Pauses the game as soon as it loads')
        pause_load.grid(column=1, row=1, sticky="nsew")
        self.controls['pauseOnLoad'] = pause_load
        backup_saves = Button(
            saverelated, text='Backup Saves',
            command=lambda: self.cycle_option('autoBackup'))
        create_tooltip(backup_saves, 'Makes a backup of every autosave')
        backup_saves.grid(column=0, row=2, sticky="nsew")
        self.controls['autoBackup'] = backup_saves
        compress_saves = Button(
            saverelated, text='Compress Saves',
            command=lambda: self.cycle_option('compressSaves'))
        create_tooltip(
            compress_saves, 'Whether to compress the savegames '
            '(keep this on unless you experience problems with your saves')
        compress_saves.grid(column=1, row=2, sticky="nsew")
        self.controls['compressSaves'] = compress_saves
        open_savegames = Button(
            saverelated, text='Open Savegame Folder',
            command=self.lnp.open_savegames)
        create_tooltip(open_savegames, 'Open the savegame folder')
        open_savegames.grid(column=0, row=3, columnspan=2, sticky="nsew")

        Frame(f, height=30).grid(column=0, row=3)
        priority = Button(
            f, text='Processor Priority',
            command=lambda: self.cycle_option('procPriority'))
        create_tooltip(
            priority, 'Adjusts the priority given to Dwarf Fortress by your OS')
        priority.grid(column=0, row=4, columnspan=2, sticky="nsew")
        self.controls['procPriority'] = priority

        closeOnLaunch = Button(
            f, text='Close GUI on launch', command=self.toggle_autoclose)
        create_tooltip(
            closeOnLaunch,
            'Whether this GUI should close when Dwarf Fortress is launched')
        closeOnLaunch.grid(column=0, row=5, columnspan=2, sticky="nsew")
        self.controls['autoClose'] = (
            closeOnLaunch,
            lambda v: ('NO', 'YES')[self.lnp.userconfig.get_bool('autoClose')])
        return f

    def create_dfhack(self, n):
        """
        Creates the DFHack tab.

        Params:
            n
                Notebook instance to create the tab in.
        """
        f = Frame(n)
        f.pack(side=TOP, fill=BOTH, expand=Y)
        hacks = Labelframe(f, text='Available hacks')
        hacks.pack(side=TOP, expand=Y, fill=BOTH)
        Grid.columnconfigure(hacks, 0, weight=1)
        Grid.rowconfigure(hacks, 1, weight=1)

        Label(
            hacks, text='Click on a hack to toggle it.').grid(
                column=0, row=0)
        listframe = Frame(hacks)
        listframe.grid(column=0, row=1, sticky="nsew")
        Grid.rowconfigure(listframe, 0, weight=1)
        Grid.columnconfigure(listframe, 0, weight=1)
        self.hacklist = hacklist = Treeview(
            listframe, columns=('name', 'enabled'), show=['headings'],
            selectmode='browse')
        hacklist.column('name', width=1, anchor='w')
        hacklist.column('enabled', width=50, anchor='c', stretch=NO)
        hacklist.heading('name', text='Hack')
        hacklist.heading('enabled', text='Enabled')
        hacklist.grid(column=0, row=0, sticky="nsew")
        hacklist.bind("<<TreeviewSelect>>", lambda e: self.toggle_hack())
        s = Scrollbar(listframe, orient=VERTICAL, command=hacklist.yview)
        hacklist['yscrollcommand'] = s.set
        s.grid(column=1, row=0, sticky="ns")

        self.hack_tooltip = create_tooltip(hacklist, '')
        hacklist.bind('<Motion>', self.update_hack_tooltip)
        return f

    def change_entry(self, key, var):
        """
        Commits a change for the control specified by key.

        Params:
            key
                The key for the control that changed.
            var
                The variable bound to the control.
        """
        if var.get() != '':
            self.lnp.set_option(key, var.get())

    def update_hack_tooltip(self, event):
        """
        Event handler for mouse motion over the hack list.
        Used to update the tooltip.
        """
        item = self.lnp.get_hack(self.hacklist.item(self.hacklist.identify(
            'row', event.x, event.y))['text'])
        if item:
            self.hack_tooltip.settext(item['tooltip'])
        else:
            self.hack_tooltip.settext('')

    def create_menu(self, root):
        """
        Creates the menu bar.

        Params:
            root
                Root window for the menu bar.
        """
        menubar = Menu(root)
        root['menu'] = menubar

        menu_file = Menu(menubar)
        menu_run = Menu(menubar)
        menu_folders = Menu(menubar)
        menu_links = Menu(menubar)
        menu_help = Menu(menubar)
        menu_beta = Menu(menubar)
        menubar.add_cascade(menu=menu_file, label='File')
        menubar.add_cascade(menu=menu_run, label='Run')
        menubar.add_cascade(menu=menu_folders, label='Folders')
        menubar.add_cascade(menu=menu_links, label='Links')
        menubar.add_cascade(menu=menu_help, label='Help')
        menubar.add_cascade(menu=menu_beta, label='Testing')

        menu_file.add_command(
            label='Re-load param set', command=self.load_params,
            accelerator='Ctrl+L')
        menu_file.add_command(
            label='Re-save param set', command=self.save_params,
            accelerator='Ctrl+S')
        menu_file.add_command(
            label='Output log', command=lambda: LogWindow(self.root))
        if sys.platform != 'darwin':
            menu_file.add_command(
                label='Exit', command=self.exit_program, accelerator='Alt+F4')
        root.bind_all('<Control-l>', lambda e: self.load_params())
        root.bind_all('<Control-s>', lambda e: self.save_params())

        menu_run.add_command(
            label='Dwarf Fortress', command=self.lnp.run_df,
            accelerator='Ctrl+R')
        menu_run.add_command(
            label='Init Editor', command=self.run_init, accelerator='Ctrl+I')
        root.bind_all('<Control-r>', lambda e: self.lnp.run_df())
        root.bind_all('<Control-i>', lambda e: self.run_init())

        for i, f in enumerate(self.lnp.config['folders']):
            if f[0] == '-':
                menu_folders.add_separator()
            else:
                menu_folders.add_command(
                    label=f[0],
                    command=lambda i=i: self.lnp.open_folder_idx(i))

        for i, f in enumerate(self.lnp.config['links']):
            if f[0] == '-':
                menu_links.add_separator()
            else:
                menu_links.add_command(
                    label=f[0],
                    command=lambda i=i: self.lnp.open_link_idx(i))

        menu_help.add_command(
            label="Help", command=self.show_help, accelerator='F1')
        menu_help.add_command(
            label="About", command=self.show_about, accelerator='Alt+F1')
        root.bind_all('<F1>', lambda e: self.show_help())
        root.bind_all('<Alt-F1>', lambda e: self.show_about())
        root.createcommand('tkAboutDialog', self.show_about)

        menu_beta.add_command(
            label='Toggle graphics pack patching', command=self.toggle_patching)

    def load_params(self):
        """Reads configuration data."""
        try:
            self.lnp.load_params()
        except IOError as e:
            messagebox.showerror(self.root.title(), e.message)
            self.exit_program()
        self.update_displays()

    def save_params(self):
        """Writes configuration data."""
        self.lnp.save_params()

    def restore_defaults(self):
        """Restores default configuration data."""
        if messagebox.askyesno(
                message='Are you sure? '
                'ALL SETTINGS will be reset to game defaults.\n'
                'You may need to re-install graphics afterwards.',
                title='Reset all settings to Defaults?', icon='question'):
            self.lnp.restore_defaults()
            messagebox.showinfo(
                self.root.title(),
                'All settings reset to defaults!')

    def exit_program(self):
        """Quits the program."""
        self.root.destroy()

    def run_program(self, path):
        """
        Launches another program.

        Params:
            path
                Path to the program to launch.
        """
        path = os.path.abspath(path)
        self.lnp.run_program(path)

    def run_init(self):
        """Opens the init editor."""
        InitEditor(self.root, self)

    @staticmethod
    def show_help():
        """Shows help for the program."""
        messagebox.showinfo(title='How to Use', message="It's really easy.")

    @staticmethod
    def show_about():
        """Shows about dialog for the program."""
        messagebox.showinfo(
            title='About', message="PyLNP - Lazy Newb Pack Python Edition\n\n"
            "Port by Pidgeot\n\nOriginal program: LucasUP, TolyK/aTolyK")

    def read_keybinds(self):
        """Reads list of keybinding files."""
        self.keybinds.set(self.lnp.read_keybinds())

    def read_graphics(self):
        """Reads list of graphics packs."""
        self.graphics.set(tuple([p[0] for p in self.lnp.read_graphics()]))

    def read_utilities(self):
        """Reads list of utilities."""
        self.progs = self.lnp.read_utilities()
        self.update_autorun_list()

    def read_colors(self):
        """Reads list of color schemes."""
        self.colors.set(self.lnp.read_colors())
        self.paint_color_preview(self.color_files)

    def read_embarks(self):
        """Reads list of embark profiles."""
        self.embarks.set(self.lnp.read_embarks())

    def toggle_autorun(self, event):
        """
        Toggles autorun for a utility.

        Params:
            event
                Data for the click event that triggered this.
        """
        self.lnp.toggle_autorun(self.proglist.item(self.proglist.identify(
            'row', event.x, event.y), 'text'))
        self.update_autorun_list()

    def update_autorun_list(self):
        """Updates the autorun list."""
        for i in self.proglist.get_children():
            self.proglist.delete(i)
        for p in self.progs:
            exe = os.path.join(
                os.path.basename(os.path.dirname(p)), os.path.basename(p))
            if self.lnp.config["hideUtilityPath"]:
                exe = os.path.splitext(os.path.basename(p))[0]
            self.proglist.insert('', 'end', text=p, values=(
                exe, 'Yes' if p in self.lnp.autorun else 'No'))

    def update_displays(self):
        """Updates configuration displays (buttons, etc.)."""
        for key in self.controls.keys():
            try:
                value = getattr(self.lnp.settings, key)
            except KeyError:
                value = None
            if hasattr(self.controls[key], '__iter__'):
                # Allow (control, func) tuples, etc. to customize value
                control = self.controls[key][0]
                value = self.controls[key][1](value)
            else:
                control = self.controls[key]
            if isinstance(control, Entry):
                control.delete(0, END)
                control.insert(0, value)
            else:
                control["text"] = (
                    control["text"].split(':')[0] + ': ' +
                    value)

    def set_pop_cap(self):
        """Requests new population cap from the user."""
        v = simpledialog.askinteger(
            "Settings", "Population cap:",
            initialvalue=self.lnp.settings.popcap, parent=self.root)
        if v is not None:
            self.lnp.set_option('popcap', v)
            self.update_displays()

    def set_child_cap(self):
        """Resquests new child cap from the user."""
        child_split = list(self.lnp.settings.childcap.split(':'))
        child_split.append('0')  # In case syntax is invalid
        v = simpledialog.askinteger(
            "Settings", "Absolute cap on babies + children:",
            initialvalue=child_split[0], parent=self.root)
        if v is not None:
            v2 = simpledialog.askinteger(
                "Settings", "Max percentage of children in fort:\n"
                "(lowest of the two values will be used as the cap)",
                initialvalue=child_split[1], parent=self.root)
            if v2 is not None:
                self.lnp.set_option('childcap', str(v)+':'+str(v2))
                self.update_displays()

    def cycle_option(self, field):
        """
        Cycles through possible values for an option.

        Params:
            field
                The option to cycle.
        """
        self.lnp.cycle_option(field)
        self.update_displays()

    def set_option(self, field):
        """
        Sets an option directly.

        Params:
            field
                The field name to change. The corresponding value is
                automatically read.
        """
        self.lnp.set_option(field, self.controls[field].get())
        self.update_displays()

    def load_keybinds(self, listbox):
        """
        Replaces keybindings with selected file.

        Params:
            listbox
                Listbox containing the list of keybinding files.
        """
        if len(listbox.curselection()) != 0:
            self.lnp.load_keybinds(listbox.get(listbox.curselection()[0]))

    def save_keybinds(self):
        """Saves keybindings to a file."""
        v = simpledialog.askstring(
            "Save Keybindings", "Save current keybindings as:",
            parent=self.root)
        if v is not None:
            if not v.endswith('.txt'):
                v = v + '.txt'
            if (not self.lnp.keybind_exists(v) or messagebox.askyesno(
                    message='Overwrite {0}?'.format(v),
                    icon='question', title='Overwrite file?')):
                self.lnp.save_keybinds(v)
                self.read_keybinds()

    def delete_keybinds(self, listbox):
        """
        Deletes a keybinding file.

        Params:
            listbox
                Listbox containing the list of keybinding files.
        """
        if len(listbox.curselection()) != 0:
            filename = listbox.get(listbox.curselection()[0])
            if messagebox.askyesno(
                    'Delete file?',
                    'Are you sure you want to delete {0}?'.format(filename)):
                self.lnp.delete_keybinds(filename)
            self.read_keybinds()

    def load_colors(self, listbox):
        """
        Replaces color scheme  with selected file.

        Params:
            listbox
                Listbox containing the list of color schemes.
        """
        if len(listbox.curselection()) != 0:
            self.lnp.load_colors(listbox.get(listbox.curselection()[0]))

    def save_colors(self):
        """Saves color scheme to a file."""
        v = simpledialog.askstring(
            "Save Color scheme", "Save current color scheme as:",
            parent=self.root)
        if v is not None:
            if (not self.lnp.color_exists(v) or messagebox.askyesno(
                    message='Overwrite {0}?'.format(v),
                    icon='question', title='Overwrite file?')):
                self.lnp.save_colors(v)
                self.read_colors()

    def delete_colors(self, listbox):
        """
        Deletes a color scheme.

        Params:
            listbox
                Listbox containing the list of color schemes.
        """
        if len(listbox.curselection()) != 0:
            filename = listbox.get(listbox.curselection()[0])
            if messagebox.askyesno(
                    'Delete file?',
                    'Are you sure you want to delete {0}?'.format(filename)):
                self.lnp.delete_colors(filename)
            self.read_colors()

    def paint_color_preview(self, listbox):
        """
        Draws a preview of the selected color scheme. If no scheme is selected,
        draws the currently installed color scheme.

        Params:
            listbox
                Listbox containing the list of color schemes.
        """
        colorscheme = None
        if len(listbox.curselection()) != 0:
            colorscheme = listbox.get(listbox.curselection()[0])
        colors = self.lnp.get_colors(colorscheme)

        self.color_preview.delete(ALL)
        for i, c in enumerate(colors):
            row = i / 8
            col = i % 8
            self.color_preview.create_rectangle(
                col*16, row*16, (col+1)*16, (row+1)*16,
                fill="#%02x%02x%02x" % c, width=0)

    def toggle_autoclose(self):
        """Toggle automatic closing of the UI when launching DF."""
        self.lnp.toggle_autoclose()
        self.update_displays()

    def update_hack_list(self):
        """Updates the hack list."""
        for i in self.hacklist.get_children():
            self.hacklist.delete(i)
        for k, h in self.lnp.get_hacks().items():
            self.hacklist.insert('', 'end', text=k, values=(
                k, 'Yes' if h['enabled'] else 'No'))

    def toggle_hack(self):
        """Toggles the selected hack."""
        for item in self.hacklist.selection():
            self.lnp.toggle_hack(self.hacklist.item(item, 'text'))
        self.update_hack_list()

    def install_embarks(self, listbox):
        """
        Installs selected embark profiles.

        Params:
            listbox
                Listbox containing the list of embark profiles.
        """
        if len(listbox.curselection()) != 0:
            files = []
            for f in listbox.curselection():
                files.append(listbox.get(f))
            self.lnp.install_embarks(files)

    def install_graphics(self, listbox):
        """
        Installs a graphics pack.

        Params:
            listbox
                Listbox containing the list of graphics packs.
        """
        if len(listbox.curselection()) != 0:
            gfx_dir = listbox.get(listbox.curselection()[0])
            if messagebox.askokcancel(
                    message='Your graphics, settings and raws will be changed.',
                    title='Are you sure?'):
                result = self.lnp.install_graphics(gfx_dir)
                if result is False:
                    messagebox.showerror(
                        title=self.root.title(),
                        message='Something went wrong: '
                        'the graphics folder may be missing important files. '
                        'Graphics may not be installed correctly.\n'
                        'See the output log for error details.')
                elif result:
                    if messagebox.askyesno(
                            'Update Savegames?',
                            'Graphics and settings installed!\n'
                            'Would you like to update your savegames to '
                            'properly use the new graphics?'):
                        self.update_savegames()
                else:
                    messagebox.showerror(
                        title=self.root.title(),
                        message='Nothing was installed.\n'
                        'Folder does not exist or does not have required files '
                        'or folders:\n'+gfx_dir)
            self.load_params()

    def update_savegames(self):
        """Updates saved games with new raws."""
        count = self.lnp.update_savegames()
        if count > 0:
            messagebox.showinfo(
                title=self.root.title(),
                message="{0} savegames updated!".format(count))
        else:
            messagebox.showinfo(
                title=self.root.title(), message="No savegames to update.")

    def simplify_graphics(self):
        """Removes unnecessary files from graphics packs."""
        self.read_graphics()
        for pack in self.graphics.get():
            result = self.lnp.simplify_pack(pack)
            if result is None:
                messagebox.showinfo(
                    title=self.root.title(), message='No files in: '+pack)
            elif result is False:
                messagebox.showerror(
                    title=self.root.title(),
                    message='Error simplifying graphics folder. '
                    'It may not have the required files.\n'+pack+'\n'
                    'See the output log for error details.')
            else:
                messagebox.showinfo(
                    title=self.root.title(),
                    message='Deleted {0} unnecessary file(s) in: {1}'.format(
                        result, pack))
        messagebox.showinfo(
            title=self.root.title(), message='Simplification complete!')

    def run_selected_utilities(self):
        """Runs selected utilities."""
        for item in self.proglist.selection():
            utility_path = self.proglist.item(item, 'text')
            self.lnp.run_program(os.path.join(self.lnp.utils_dir, utility_path))

    def toggle_patching(self):
        """Toggles the use of patchingfor installing graphics packs."""
        if self.lnp.install_inits == self.lnp.copy_inits:
            self.lnp.install_inits = self.lnp.patch_inits
            messagebox.showinfo(
                title=self.root.title(),
                message='Enabled patching of init.txt and d_init.txt during '
                'installation of graphics packs. Note: This is still an '
                'experimental feature; backup your files first.')
        else:
            self.lnp.install_inits = self.lnp.copy_inits
            messagebox.showinfo(
                title=self.root.title(),
                message='Disabled patching of init.txt and d_init.txt during '
                'installation of graphics packs. Files will be replaced.')

# vim:expandtab
