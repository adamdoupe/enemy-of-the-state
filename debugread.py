#!/usr/bin/env python

import gtk
import re

colmap = {
        (1, 1): "#ff0000",
        (1, 6): "#cc0000",
        (2, 1): "#00ff00",
        (3, 1): "#ffff00",
        (4, 1): "#5555ff",
        (5, 1): "#ff00ff",
        (5, 6): "#cc00cc",
        (6, 1): "#00ffff",
        (6, 6): "#00cccc",
        }

class LogReader(object):

    def __init__(self, logfile):
        self.window = window = gtk.Window(gtk.WINDOW_TOPLEVEL)

        window.connect("delete_event", self.delete_event)
        window.connect("destroy", self.destroy)

        window.set_default_size(1000, 700)

        self.textview = textview = gtk.TextView(buffer=None)
        textview.set_editable(False)
        textview.modify_base(gtk.STATE_NORMAL, gtk.gdk.color_parse("#000000"))
        textview.modify_text(gtk.STATE_NORMAL, gtk.gdk.color_parse("#ffffff"))

        self.textbuffer = textbuffer = textview.get_buffer()

        coltagmap = {}

        for c, g in colmap.iteritems():
            tag = textbuffer.create_tag(foreground=g)
            coltagmap[c] = tag


        colorre = re.compile(r'\x1b\x5b[^m]*m')
        valsre = re.compile(r'\x1b\x5b([0-9]+)(?:;([0-9]+))*m')
        with open(logfile, 'r') as f:
            text = f.read()

        start = 0
        nexttag = None
        it = textbuffer.get_iter_at_offset(0)
        for m in colorre.finditer(text):
            if nexttag:
                textbuffer.insert_with_tags(it, text[start:m.start()], nexttag)
            else:
                textbuffer.insert(it, text[start:m.start()])
            mm = valsre.match(m.group(0))
            mainattr = int(mm.group(1))
            if mainattr >= 30:
                assert mainattr <= 37
                col1 = mainattr - 30
                col2 = int(mm.group(2)) if mm.group(1) else 0
                nexttag = coltagmap[(col1, col2)]
            else:
                assert mainattr == 0
                nexttag = None
            start = m.end()

        del text

        sw = gtk.ScrolledWindow()
        sw.add(textview)
        window.add(sw)

        textview.show()
        sw.show()
        window.show()


    def destroy(self, widget, data=None):
        gtk.main_quit()


    def delete_event(self, widget, event, data=None):
        return False


    def main(self):
        gtk.main()


if __name__ == "__main__":
    import sys
    logreader = LogReader(sys.argv[1])
    logreader.main()
