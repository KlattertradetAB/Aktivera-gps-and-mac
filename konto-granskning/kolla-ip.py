#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kolla-ip.py — slå upp vart DINA EGNA inloggnings-IP:n pekar (land/region/operatör).

Det här är din egen kontodata (inloggningar på ditt eget konto). Skriptet gör
bara publika uppslag mot öppna geo-IP-tjänster. Det ger land, region och
operatör — INTE en persons identitet eller exakta adress (det går bara via
polis + operatör).

Kör på din egen dator (där internet är öppet):
    python3 kolla-ip.py

Endast standardbiblioteket.
"""

import json
import urllib.request

# Klistra in dina egna inloggnings-IP:n här:
IPN = [
    "90.129.218.143",
    "90.129.193.210",
    "90.129.207.175",
    "90.130.62.170",
]


def sla_upp(ip):
    url = f"https://ipapi.co/{ip}/json/"
    req = urllib.request.Request(url, headers={"User-Agent": "ip-kontroll/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.load(r)


def main():
    print(f"{'IP':<17} {'Land':<10} {'Region':<18} {'Stad (grov)':<18} Operatör")
    print("-" * 80)
    for ip in IPN:
        try:
            d = sla_upp(ip)
            print(f"{ip:<17} {str(d.get('country_name','?'))[:9]:<10} "
                  f"{str(d.get('region','?'))[:17]:<18} "
                  f"{str(d.get('city','?'))[:17]:<18} "
                  f"{d.get('org','?')}")
        except Exception as e:
            print(f"{ip:<17} (uppslag misslyckades: {e})")
    print("\nOBS: Stad/region för mobila IP:n pekar på operatörens gateway,")
    print("inte på var personen faktiskt befinner sig. Bara operatören (Tele2)")
    print("vet vem som hade adressen — och det lämnas bara ut till polis.")


if __name__ == "__main__":
    main()
