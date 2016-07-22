#! /usr/bin/env python2
# coding:UTF-8

import os
import sys
import datetime
import traceback

sys.path.insert(0, os.path.dirname(__file__))

try:
    import Tkinter as tk
    import tkMessageBox
    import tkFileDialog

except:
    tkMessageBox.showwarning("Error", "Tkinter is not correctly installed !")
    sys.exit()

try:
    import bp_connect
except:
    tkMessageBox.showwarning("Missing file", "bp_connect.py is missing")
    sys.exit()

try:
    import bp_custo
    from bp_custo import windows_title, errors_text, buttons_text, menus_text, labels_text
except:
    tkMessageBox.showwarning("Missing file", "bp_custo.py is missing")
    sys.exit()

try:
    import bp_Dialog
except:
    tkMessageBox.showwarning("Missing file", "bp_Dialog.py is missing")
    sys.exit()

try:
    from bp_widgets import ListboxWidget, EntryWidget, OptionWidget
except:
    tkMessageBox.showwarning("Missing file", "bp_widgets.py is missing")
    sys.exit()

try:
    from dateutil.parser import parse as du_parse, parserinfo
except:
    tkMessageBox.showwarning(u"Missing dependency", u"The dateutil module is missing")
    sys.exit()


class FrenchParserInfo(parserinfo):
    MONTHS = [(u'jan', u'janvier'), (u'fév', u'février'), (u'mar', u'mars'), (u'avr', u'avril'), (u'mai', u'mai'), (u'jui', u'juin'), (u'jul', u'juillet'), (u'aoû', u'août'), (u'sep', u'septembre'), (u'oct', u'octobre'), (u'nov', u'novembre'), (u'déc', u'décembre')]
    WEEKDAYS = [(u'Lun', u'Lundi'), (u'Mar', u'Mardi'), (u'Mer', u'Mercredi'), (u'Jeu', u'Jeudi'), (u'Ven', u'Vendredi'), (u'Sam', u'Samedi'), (u'Dim', u'Dimanche')]
    HMS = [(u'h', u'heure', u'heures'), (u'm', u'minute', u'minutes'), (u's', u'seconde', u'secondes')]
    JUMP = [u' ', u'.', u',', u';', u'-', u'/', u"'", u"le", u"er", u"ième"]

datesFR = FrenchParserInfo(dayfirst=True)
MIN_DATE = datetime.date(1900, 1, 1)  # Cannot strftime before that date


def parse_date(s):
    d = du_parse(s, parserinfo=datesFR).date()
    if d < MIN_DATE:
        raise ValueError("Date too old")
    return d

try:
    import MySQLdb
except:
    tkMessageBox.showwarning("Error", "Module mysqldb is not correctly installed !")
    sys.exit()

try:
    db = MySQLdb.connect(host=bp_connect.serveur, user=bp_connect.identifiant, passwd=bp_connect.secret, db=bp_connect.base, charset='latin1')
except:
    tkMessageBox.showwarning("MySQL", "Cannot connect to database")
    sys.exit()

db.autocommit(True)
cursor = db.cursor()


class apropos(bp_Dialog.Dialog):
    def body(self, master):
        self.title(windows_title.apropos)
        self.geometry('+350+250')
        tk.Label(master, text=labels_text.apropos_description, font=("Helvetica", 13, 'bold')).grid(row=0, column=0, sticky=tk.W)


class licence(bp_Dialog.Dialog):
    def body(self, master):
        self.title(windows_title.licence)
        self.geometry('+350+250')
        tk.Label(master, text=labels_text.licence_description, font=("Helvetica", 13, 'bold')).grid(row=0, column=0, sticky=tk.W)


def sum_found(positions):
    return sum(p[6] for p in positions) / 100.0


def sum_notfound(positions):
    return sum(p[3] for p in positions) / 100.0


class SummariesImport(bp_Dialog.Dialog):
    def __init__(self, parent, ok, ko, doubled, not_found, ignored):
        self.ok = ok
        self.ko = ko
        self.doubled = doubled
        self.not_found = not_found
        self.ignored = ignored
        bp_Dialog.Dialog.__init__(self, parent)

    def buttonbox(self):
        box = tk.Frame(self)
        tk.Button(box, text=buttons_text.valider_import, command=self.validate).pack(side=tk.LEFT)
        tk.Button(box, text=buttons_text.cancel, command=self.cancel).pack(side=tk.LEFT)
        self.bind("<Escape>", self.cancel)
        box.pack()

    def validate(self):
        try:
            for payment in self.ok:
                id_consult = payment[0]
                credit_date = payment[10]
                cursor.execute("UPDATE consultations SET paye_le = %s WHERE id_consult = %s", [credit_date, id_consult])
            self.cancel()
        except:
            traceback.print_exc()
            tkMessageBox.showwarning(windows_title.db_error, errors_text.db_update)

    def body(self, master):
        self.title(windows_title.summaries_import)
        tk.Label(master, text=u"Volume").grid(row=0, column=1)
        tk.Label(master, text=u"Revenu").grid(row=0, column=2)

        tk.Label(master, text=u"Payements en ordre").grid(row=1, column=0)
        tk.Label(master, text=str(len(self.ok))).grid(row=1, column=1)
        tk.Label(master, text=u"%0.2f CHF" % sum_found(self.ok)).grid(row=1, column=2, sticky=tk.E)
        if self.ok:
            tk.Button(master, text=buttons_text.details, command=lambda: Details(self, self.ok)).grid(row=1, column=3, sticky=tk.W)

        tk.Label(master, text=u"Payements ne correspondant pas au montant attendu").grid(row=2, column=0)
        tk.Label(master, text=str(len(self.ko))).grid(row=2, column=1)
        tk.Label(master, text=u"%0.2f CHF" % sum_found(self.ko)).grid(row=2, column=2, sticky=tk.E)
        if self.ko:
            tk.Button(master, text=buttons_text.details, command=lambda: Details(self, self.ko)).grid(row=2, column=3, sticky=tk.W)

        tk.Label(master, text=u"Payements déjà encaissés").grid(row=3, column=0)
        tk.Label(master, text=str(len(self.doubled))).grid(row=3, column=1)
        tk.Label(master, text=u"%0.2f CHF" % sum_found(self.doubled)).grid(row=3, column=2, sticky=tk.E)
        if self.doubled:
            tk.Button(master, text=buttons_text.details, command=lambda: Details(self, self.doubled)).grid(row=3, column=3, sticky=tk.W)

        tk.Label(master, text=u"Payements non trouvés").grid(row=4, column=0)
        tk.Label(master, text=str(len(self.not_found))).grid(row=4, column=1)
        tk.Label(master, text=u"%0.2f CHF" % sum_notfound(self.not_found)).grid(row=4, column=2, sticky=tk.E)
        if self.not_found:
            tk.Button(master, text=buttons_text.details, command=lambda: Details(self, self.not_found)).grid(row=4, column=3, sticky=tk.W)

        tk.Label(master, text=u"Ordres ignorés").grid(row=5, column=0)
        tk.Label(master, text=str(len(self.ignored))).grid(row=5, column=1)
        if self.ignored:
            tk.Button(master, text=buttons_text.details, command=lambda: Details(self, self.ignored)).grid(row=5, column=3, sticky=tk.W)

        master.grid_columnconfigure(0, weight=1)
        master.grid_columnconfigure(1, weight=1)
        master.grid_columnconfigure(2, weight=1)


class Details(bp_Dialog.Dialog):
    transaction_types = {
        '002': u'Crédit B préimp', '005': u'Extourne B préimp', '008': u'Correction B préimp',
        '012': u'Crédit P préimp', '015': u'Extourne P préimp', '018': u'Correction P préimp',
        '102': u'Crédit B', '105': u'Extourne B', '108': u'Correction B',
        '112': u'Crédit P', '115': u'Extourne P', '118': u'Correction P',
    }

    def __init__(self, parent, positions):
        self.positions = positions
        bp_Dialog.Dialog.__init__(self, parent)

    def buttonbox(self):
        self.bind("<Escape>", self.cancel)
        return tk.Button(self, text=buttons_text.done, command=self.cancel)

    def body(self, master):
        hscroll = tk.Scrollbar(master, orient=tk.HORIZONTAL)
        vscroll = tk.Scrollbar(master, orient=tk.VERTICAL)
        self.list_box = tk.Listbox(master, xscrollcommand=hscroll.set, yscrollcommand=vscroll.set, font=(bp_custo.FIXED_FONT_NAME, 10))
        hscroll.config(command=self.list_box.xview)
        vscroll.config(command=self.list_box.yview)
        self.list_box.grid(row=0, column=0, sticky=tk.NSEW)
        hscroll.grid(row=1, column=0, sticky=tk.EW)
        vscroll.grid(row=0, column=1, sticky=tk.NS)
        master.grid_rowconfigure(0, weight=1)
        master.grid_columnconfigure(0, weight=1)

        if len(self.positions[0]) == 14:
            self.populate_found()
        else:
            self.populate_notfound()

    def format_date(self, date):
        if date is None:
            return u''
        elif isinstance(date, basestring):
            return u'20' + date[:2] + u'-' + date[2:4] + u'-' + date[4:]
        return unicode(date)

    def format_ref(self, ref):
        ref = list(ref)
        for pos in (2, 8, 14, 20, 26):
            ref.insert(pos, ' ')
        return ''.join(ref)

    def populate_found(self):
        self.list_box.delete(0, tk.END)
        data = []
        columns = [u"Sex", u"Nom", u"Prénom", u"Naissance", u"Consultation du", u"Facturé CHF", u"Payé CHF", u"Crédité le", u"Comtabilisé le", u"Numéro de référence"]
        widths = [len(c) for c in columns]
        for id_consult, prix_cts, majoration_cts, transaction_type, bvr_client_no, ref_no, amount_cts, depot_ref, depot_date, processing_date, credit_date, microfilm_no, reject_code, postal_fee_cts in self.positions:
            cursor.execute("SELECT sex, nom, prenom, date_naiss, date_consult, paye_le FROM consultations INNER JOIN patients ON patients.id = consultations.id WHERE id_consult = %s", [id_consult])
            sex, nom, prenom, date_naiss, date_consult, paye_le = cursor.fetchone()
            data.append((sex, nom, prenom, date_naiss, date_consult, u'%0.2f' % ((prix_cts+majoration_cts)/100.), u'%0.2f' % (amount_cts/100.), self.format_date(credit_date), self.format_date(paye_le), self.format_ref(ref_no)))
            widths = [max(a, len(unicode(b))) for a, b in zip(widths, data[-1])]
        self.list_box.config(width=min(120, sum(widths)+2*9))
        widths[5] *= -1
        widths[6] *= -1

        self.list_box.insert(tk.END, u"  ".join(u"%*s" % (-w, c) for w, c in zip(widths, columns)))
        for values in data:
            self.list_box.insert(tk.END, u"  ".join(u"%*s" % (-w, unicode(v)) for w, v in zip(widths, values)))

    def populate_notfound(self):
        self.list_box.delete(0, tk.END)
        data = []
        columns = [u"Type de transaction", u"Payé CHF", u"Crédité le", u"Numéro de référence"]
        widths = [len(c) for c in columns]
        for transaction_type, bvr_client_no, ref_no, amount_cts, depot_ref, depot_date, processing_date, credit_date, microfilm_no, reject_code, postal_fee_cts in self.positions:
            data.append((self.transaction_types.get(transaction_type, transaction_type), u'%0.2f' % (amount_cts/100.), self.format_date(credit_date), self.format_ref(ref_no)))
            widths = [max(a, len(unicode(b))) for a, b in zip(widths, data[-1])]
        self.list_box.config(width=sum(widths)+2*3)
        widths[1] *= -1

        self.list_box.insert(tk.END, u"  ".join(u"%*s" % (-w, c) for w, c in zip(widths, columns)))
        for values in data:
            self.list_box.insert(tk.END, u"  ".join(u"%*s" % (-w, unicode(v)) for w, v in zip(widths, values)))


class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        if (sys.platform != 'win32') and hasattr(sys, 'frozen'):
            self.tk.call('console', 'hide')

        self.option_add('*font', 'Helvetica -15')
        self.title(windows_title.compta)

        menubar = tk.Menu(self)

        bvrmenu = tk.Menu(menubar, tearoff=0)
        bvrmenu.add_command(label=menus_text.import_bvr, command=self.import_bvr)

        menubar.add_cascade(label=menus_text.bvr, menu=bvrmenu)

        helpmenu = tk.Menu(menubar, tearoff=0)
        helpmenu.add_command(label=menus_text.about, command=lambda: apropos(self))
        helpmenu.add_command(label=menus_text.licence, command=lambda: licence(self))

        menubar.add_cascade(label=menus_text.help, menu=helpmenu)
        self.config(menu=menubar)

        try:
            cursor.execute("SELECT therapeute FROM therapeutes ORDER BY therapeute")
            therapeutes = ['Tous'] + [t for t, in cursor]
        except:
            traceback.print_exc()
            tkMessageBox.showwarning(windows_title.db_error, errors_text.db_read)
            sys.exit(1)

        # Top block: select what to display
        today = datetime.date.today()
        month_end = datetime.date(today.year, today.month, 1) - datetime.timedelta(days=1)
        last_month = datetime.date(month_end.year, month_end.month, 1)
        self.therapeute = OptionWidget(self, 'therapeute', 0, 0, therapeutes, value='Tous')
        self.paye_par = OptionWidget(self, 'paye_par', 1, 0, [''] + bp_custo.MOYEN_DE_PAYEMENT + bp_custo.ANCIEN_MOYEN_DE_PAYEMENT, value='')
        self.date_du, w_date_du = EntryWidget(self, 'date_du', 0, 2, value=last_month, want_widget=True)
        self.date_au, w_date_au = EntryWidget(self, 'date_au', 1, 2, want_widget=True)
        self.etat = OptionWidget(self, 'etat_payement', 2, 0, bp_custo.ETAT_PAYEMENT, value='Tous')
        self.therapeute.trace('w', self.update_list)
        self.paye_par.trace('w', self.update_list)
        w_date_du.bind('<KeyRelease-Return>', self.date_du_changed)
        w_date_au.bind('<KeyRelease-Return>', self.update_list)
        self.etat.trace('w', self.update_list)
        tk.Button(self, text="📅", command=lambda: self.popup_calendar(self.date_du, w_date_du), borderwidth=0, relief=tk.FLAT).grid(row=0, column=4)
        tk.Button(self, text="📅", command=lambda: self.popup_calendar(self.date_au, w_date_au), borderwidth=0, relief=tk.FLAT).grid(row=1, column=4)
        self.nom, widget = EntryWidget(self, 'nom', 3, 0, want_widget=True)
        widget.bind('<Return>', self.update_list)
        self.prenom, widget = EntryWidget(self, 'prenom', 3, 2, want_widget=True)
        widget.bind('<Return>', self.update_list)
        tk.Button(self, text="🔎", command=self.update_list, borderwidth=0, relief=tk.FLAT).grid(row=3, column=4)

        # Middle block: list display
        tk.Label(self, font=bp_custo.LISTBOX_DEFAULT,
                 text="       Nom                            Prénom                    Consultation du   Prix Payé le").grid(row=4, column=0, columnspan=4, sticky=tk.W)
        self.list_format = "%-6s %-30s %-30s %s %6.2f %s"
        self.list = ListboxWidget(self, 'consultations', 5, 0, columnspan=5)
        self.list.config(selectmode=tk.MULTIPLE)
        self.total = EntryWidget(self, 'total', 6, 2, readonly=True)

        # Bottom block: available action on selected items
        self.paye_le = EntryWidget(self, 'paye_le', 7, 0, value=today)
        tk.Button(self, text=buttons_text.mark_paye, command=self.mark_paid).grid(row=7, column=2, sticky=tk.W)

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=1)
        self.grid_rowconfigure(5, weight=2)
        self.update_list()

    def date_du_changed(self, *args):
        self.date_au.set(self.date_du.get().strip())
        self.update_list()

    def update_list(self, *args):
        therapeute = self.therapeute.get()
        paye_par = self.paye_par.get()
        date_du = parse_date(self.date_du.get().strip())
        date_au = parse_date(self.date_au.get().strip())
        etat = self.etat.get().encode('UTF-8')
        prenom = self.prenom.get().strip()
        nom = self.nom.get().strip()
        conditions = ['TRUE']
        args = []
        if therapeute != 'Tous':
            conditions.append('consultations.therapeute = %s')
            args.append(therapeute)
        if paye_par != '':
            conditions.append('paye_par = %s')
            args.append(paye_par)
        if date_du:
            conditions.append('date_consult >= %s')
            args.append(date_du)
        if date_au:
            conditions.append('date_consult < %s')
            args.append(date_au + datetime.timedelta(days=1))
        if etat == 'Comptabilisé':
            conditions.append('paye_le IS NOT NULL')
        elif etat == 'Non-comptabilisé':
            conditions.append('paye_le IS NULL')
        if prenom:
            conditions.append('prenom LIKE %s')
            args.append(prenom.replace('*', '%'))
        if nom:
            conditions.append('nom LIKE %s')
            args.append(nom.replace('*', '%'))
        self.list.delete(0, tk.END)
        self.list.selection_clear(0, tk.END)
        self.total.set('')
        self.data = []
        total = 0
        try:
            cursor.execute("""SELECT id_consult, date_consult, paye_le, prix_cts, majoration_cts, sex, nom, prenom
                                FROM consultations INNER JOIN patients ON consultations.id = patients.id
                               WHERE %s""" % ' AND '.join(conditions), args)
            for id_consult, date_consult, paye_le, prix_cts, majoration_cts, sex, nom, prenom in cursor:
                self.list.insert(tk.END, self.list_format % (sex, nom, prenom, date_consult, (prix_cts+majoration_cts)/100., paye_le))
                self.data.append(id_consult)
                total += prix_cts + majoration_cts
        except:
            traceback.print_exc()
            tkMessageBox.showwarning(windows_title.db_error, errors_text.db_read)
        self.total.set('%0.2f CHF' % (total/100.))

    def mark_paid(self, *args):
        paye_le = parse_date(self.paye_le.get())
        ids = [id_consult for i, id_consult in enumerate(self.data) if self.list.selection_includes(i)]
        try:
            if len(ids) > 1:
                cursor.execute("""UPDATE consultations SET paye_le = %s
                                WHERE paye_le IS NULL AND id_consult IN %s""",
                               [paye_le, tuple(ids)])
            elif len(ids) == 1:
                cursor.execute("""UPDATE consultations SET paye_le = %s WHERE id_consult = %s""", [paye_le, ids[0]])
        except:
            traceback.print_exc()
            tkMessageBox.showwarning(windows_title.db_error, errors_text.db_update)
        self.update_list()

    def popup_calendar(self, var, widget):
        import ttkcalendar
        geometry = widget.winfo_geometry()
        geometry = geometry[geometry.find('+'):]
        win = tk.Toplevel(self)
        win.geometry(geometry)
        win.title("Date")
        win.transient(self)
        date = parse_date(var.get())
        ttkcal = ttkcalendar.Calendar(win, locale="fr_CH.UTF-8", year=date.year, month=date.month)
        ttkcal.pack(expand=1, fill='both')
        win.update()
        win.wait_window()
        if ttkcal.selection:
            var.set(ttkcal.selection.strftime("%Y-%m-%d"))
            if var == self.date_du:
                self.date_au.set(self.date_du.get())
            self.update_list()

    def import_bvr(self):
        filename = tkFileDialog.askopenfilename(title=menus_text.import_bvr)
        if not filename:
            return
        records = []
        total_line = None
        with open(filename) as f:
            try:
                line_no = 0
                for line in f:
                    line_no += 1
                    transaction_type, line = line[:3], line[3:]
                    bvr_client_no, line = line[:9], line[9:]
                    ref_no, line = line[:27], line[27:]
                    if transaction_type[0] in '01' and transaction_type[1] in '01' and transaction_type[2] in '258':
                        amount_cts, line = int(line[:10]), line[10:]
                        if transaction_type[2] == '5':
                            amount_cts = -amount_cts
                        depot_ref, line = line[:10], line[10:]
                        depot_date, line = line[:6], line[6:]
                        processing_date, line = line[:6], line[6:]
                        credit_date, line = line[:6], line[6:]
                        microfilm_no, line = line[:9], line[9:]
                        reject_code, line = line[:1], line[1:]
                        zeros, line = line[:9], line[9:]
                        postal_fee_cts, line = int(line[:4]), line[4:].strip()
                        records.append((transaction_type, bvr_client_no, ref_no, amount_cts, depot_ref, depot_date, processing_date, credit_date, microfilm_no, reject_code, postal_fee_cts))
                    elif transaction_type in ('995', '999'):
                        total_cts, line = int(line[:12]), line[12:]
                        if transaction_type == '995':
                            total_cts = -total_cts
                        count, line = int(line[:12]), line[12:]
                        date, line = line[:6], line[6:]
                        postal_fees_cts, line = int(line[:9]), line[9:]
                        hw_postal_fees_cts, line = int(line[:9]), line[9:]
                        reserved, line = line[:13], line[13:].strip()
                        assert total_line is None, "Multiple total line found"
                        total_line = (transaction_type, bvr_client_no, ref_no, total_cts, count, date, postal_fees_cts, hw_postal_fees_cts)
                    assert line in ('', '\n'), "Garbage at end of line %d" % line_no
                assert total_line is not None and len(records) == count, "Records count does not match total line indication"
            except Exception, e:
                print e
                tkMessageBox.showerror("Fichier corrompu", "Une erreur s'est produite lors de la lecture du fichier de payement.\n%r" % e.args)
                return
        ignored = []
        not_found = []
        ok = []
        ko = []
        doubled = []
        for transaction_type, bvr_client_no, ref_no, amount_cts, depot_ref, depot_date, processing_date, credit_date, microfilm_no, reject_code, postal_fee_cts in records:
            if transaction_type[2] != '2':
                ignored.append((transaction_type, bvr_client_no, ref_no, amount_cts, depot_ref, depot_date, processing_date, credit_date, microfilm_no, reject_code, postal_fee_cts))
                continue
            cursor.execute("SELECT id_consult, prix_cts, majoration_cts, paye_le FROM consultations WHERE bv_ref = %s", [ref_no])
            if cursor.rowcount == 0:
                not_found.append((transaction_type, bvr_client_no, ref_no, amount_cts, depot_ref, depot_date, processing_date, credit_date, microfilm_no, reject_code, postal_fee_cts))
                continue
            id_consult, prix_cts, majoration_cts, paye_le = cursor.fetchone()
            if prix_cts + majoration_cts != amount_cts:
                l = ko
            elif paye_le is None:
                l = ok
            else:
                l = doubled
            l.append((id_consult, prix_cts, majoration_cts, transaction_type, bvr_client_no, ref_no, amount_cts, depot_ref, depot_date, processing_date, credit_date, microfilm_no, reject_code, postal_fee_cts))

        SummariesImport(self, ok, ko, doubled, not_found, ignored)
        self.update_list()


app = Application()
app.mainloop()
