#!/usr/bin/env python

from optparse import OptionParser
import os
import sys
import webbrowser

from mako.template import Template
from mako import exceptions
import gnucash
from gnucash import gnucash_business

class BusinessSlots(object):
    def __init__(self, book):
        self._slots = {
            #'logo':"/home/simon/EOI/heodocs/logos/EOILogoWithBackground.png",
            'logo':"/home/simon/EOI/heoDocs/logos/eoilogo.png",
            "Company ID" : "45-2485052",
            'Company Name' : "ElectroOptical Innovations",
            'Company Contact Person': "Simon Hobbs",
            'Company Email Address': "info@electrooptical.net",
            'Company Phone Number' : "(914) 236-3005",
            'Company Address' : "\n".join(["160 N State Road Suite 203", "Briarcliff Manor, NY 10510"]),
            'Company Website URL': "electrooptical.net",
        }
    def __getitem__(self, key):
        val = self._slots[key]
        #kvpv = libgnc_qof.kvp_frame_get_slot_path(self._slots, 'options', 'Business', key, None)
        #val = libgnc_qof.kvp_value_get_string(kvpv)
        return val


class Entry(object):
    @staticmethod
    def from_gnc_entry(gnc_entry):
        entry = Entry()
        entry.date = gnc_entry.GetDate()
        entry.desc = gnc_entry.GetDescription()#.encode('utf-8')
        entry.units = gnc_entry.GetAction()
        entry.qty = gnc_entry.GetQuantity().to_double()
        entry.unit_cost = gnc_entry.GetInvPrice().to_double()
        entry.discount = int(gnc_entry.GetInvDiscount().to_double())
        entry.subtotal = entry.qty * entry.unit_cost
        entry.total = (entry.subtotal * (1 - 1.0 / entry.discount)
                       if entry.discount else entry.subtotal)

        return entry


class Customer(object):
    def __init__(self):
        self.name = None
        self.contact = None
        self.email = None
        self.phone = None
        self.addr = []

    @staticmethod
    def from_gnc_customer(gnc_customer):
        customer = Customer()
        customer.name = gnc_customer.GetName()
        customer.contact = gnc_customer.GetAddr().GetName()
        customer.email = gnc_customer.GetAddr().GetEmail()
        customer.phone = gnc_customer.GetAddr().GetPhone()
        addr = [
            gnc_customer.GetAddr().GetAddr1(),
            gnc_customer.GetAddr().GetAddr2(),
            gnc_customer.GetAddr().GetAddr3(),
            gnc_customer.GetAddr().GetAddr4(),
        ]
        customer.address = [a for a in addr if a != ""]
        return customer


class Vendor(object):
    pass


class Job(object):
    def __init__(self):
        self.name = None
        self.reference = None

    @staticmethod
    def from_gnc_job(gnc_job):
        job = Job()
        job.name = gnc_job.GetName()
        job.reference = gnc_job.GetReference()
        return job


class UnknownOwnerType(Exception): pass


class Invoice(object):
    def __init__(self):
        self.job = Job()
        self.customer = Customer()

    @staticmethod
    def from_gnc_invoice(gnc_inv, slots):
        invoice = Invoice()
        # This returns a `Customer` object when Job is None
        owner = gnc_inv.GetOwner()
        if owner is not None:
            if isinstance(owner, gnucash_business.Customer):
                invoice.customer = Customer.from_gnc_customer(owner)
            elif isinstance(owner, gnucash_business.Job):
                invoice.job = Job.from_gnc_job(owner)
                customer = owner.GetOwner()
                invoice.customer = Customer.from_gnc_customer(customer)
            else:
                raise UnknownOwnerType(type(owner))
        invoice.number = gnc_inv.GetID()
        invoice.date_opened = gnc_inv.GetDateOpened()
        invoice.date_posted = gnc_inv.GetDatePosted()
        invoice.date_due = gnc_inv.GetDateDue()
        invoice.subtotal = gnc_inv.GetTotalSubtotal().to_double()
        invoice.total = gnc_inv.GetTotal().to_double()
        invoice.total_tax = gnc_inv.GetTotalTax().to_double()
        invoice.billing_id = gnc_inv.GetBillingID()
        # NOTE This should probably be "Company" and not "Vendor"
        vendor = Vendor()
        # NOTE These may need to support internationalization
        vendor.employer_id = slots['Company ID']
        vendor.name = slots['Company Name']
        vendor.contact = slots['Company Contact Person']
        vendor.email = slots['Company Email Address']
        vendor.phone = slots['Company Phone Number']
        addr = slots['Company Address']
        vendor.address = addr.split('\n') if addr is not None else []
        vendor.website = slots['Company Website URL']
        vendor.logo = slots['logo']
        invoice.vendor = vendor
        invoice.entries = []
        for gnc_entry in gnc_inv.GetEntries():
            entry = Entry.from_gnc_entry(gnc_entry)
            invoice.entries.append(entry)
        return invoice

def GetInvoice(gca, invoice_id):
    session = gnucash.Session(gca,ignore_lock=True)
    root_account = session.book.get_root_account()
    slots = BusinessSlots(session.book)
    i = session.book.InvoiceLookupByID(invoice_id)
    if i is None:
        raise UserWarning("Failed to lookup invoice '%s'" % invoice_id)
    invoice = Invoice.from_gnc_invoice(i, slots)
    return invoice

def makeHTML(gca, invoice_id, template):
    if(True):
        invoice = GetInvoice(gca, invoice_id)
        t = Template(filename=template)
        out_path = 'invoice_%s.html' % invoice_id
        try:
            with open(out_path, 'w') as f:
                f.write(
                    t.render_unicode(invoice=invoice).encode('utf-8').decode('utf-8')
                )
        except Exception:
            print(exceptions.text_error_template().render())
            raise
        else:
            return
            webbrowser.open("file://" + os.path.join(os.path.abspath(os.curdir), out_path))

import click

@click.command()
@click.option("--gca", "-g", required=True, help="Gnucash file")
@click.option("--invoice", "-i", required=True, help="Invoice ID")
@click.option("--template", "-t", required=True, help="Template")
def main(gca, invoice, template):
    makeHTML(gca, invoice, template)


if __name__ == '__main__':
    main()
