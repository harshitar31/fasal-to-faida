# -*- coding: utf-8 -*-
"""
strings.py
==========
All bot messages in all supported languages.
To add a new language: add its code to LANGS and a new key to every STRINGS entry.
"""

# Map user reply digit → internal language code
LANGS = {"1": "EN", "2": "HI", "3": "TA"}

# First message shown to any new user (multilingual so everyone can read it)
LANG_MENU = (
    "Fasal-to-Faida\n"
    "Select language / \u092d\u093e\u0937\u093e \u091a\u0941\u0928\u0947\u0902 / \u0bae\u0bca\u0bb4\u0bbf \u0ba4\u0bc7\u0bb0\u0bcd\u0bb5\u0bc1:\n"
    "1. English\n"
    "2. \u0939\u093f\u0928\u094d\u0926\u0940\n"
    "3. \u0ba4\u0bae\u0bbf\u0bb4\u0bcd"
)

# Crop display names per language (order matches ALL_CROPS list)
CROP_NAMES = {
    "Tomato": {"EN": "Tomato",              "HI": "\u0924\u092e\u093e\u0924\u0930",         "TA": "\u0ba4\u0b95\u0bcd\u0b95\u0bbe\u0bb3\u0bbf"},
    "Onion":  {"EN": "Onion",               "HI": "\u092a\u094d\u092f\u093e\u091c",           "TA": "\u0bb5\u0bc6\u0b99\u0bcd\u0b95\u0bbe\u0baf\u0bae\u0bcd"},
    "Potato": {"EN": "Potato",              "HI": "\u0906\u0932\u0942",            "TA": "\u0b89\u0bb0\u0bc1\u0bb3\u0bc8\u0b95\u0bcd\u0b95\u0bbf\u0bb4\u0b99\u0bcd\u0b95\u0bc1"},
    "Wheat":  {"EN": "Wheat",               "HI": "\u0917\u0947\u0939\u0942\u0901",          "TA": "\u0b95\u0bcb\u0ba4\u0bcd\u0ba4\u0bc1\u0bae\u0bc8"},
    "Rice":   {"EN": "Rice",                "HI": "\u091a\u093e\u0935\u0932",           "TA": "\u0b85\u0bb0\u0bbf\u0b9a\u0bbf"},
}

STRINGS = {
    # Language confirmed
    "lang_set": {
        "EN": "Language set: English\n\n{next}",
        "HI": "\u092d\u093e\u0937\u093e: \u0939\u093f\u0928\u094d\u0926\u0940\n\n{next}",
        "TA": "\u0bae\u0bca\u0bb4\u0bbf: \u0ba4\u0bae\u0bbf\u0bb4\u0bcd\n\n{next}",
    },

    # Lang switch confirmation (LANG N command)
    "lang_switched": {
        "EN": "Language set to English.",
        "HI": "\u092d\u093e\u0937\u093e \u0939\u093f\u0928\u094d\u0926\u0940 \u0915\u0930 \u0926\u0940 \u0917\u0908 \u0939\u0948\u0964",
        "TA": "\u0bae\u0bca\u0bb4\u0bbf \u0ba4\u0bae\u0bbf\u0bb4\u0bbe\u0b95 \u0bae\u0bbe\u0bb1\u0bcd\u0bb1\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f\u0ba4\u0bc1.",
    },

    # Registration prompt (shown after language is set or on MENU for unregistered)
    "register_prompt": {
        "EN": "Register your district:\nSend #PINCODE\nExample: #641001",
        "HI": "\u0905\u092a\u0928\u093e \u091c\u093f\u0932\u093e \u0926\u0930\u094d\u091c \u0915\u0930\u0947\u0902:\n#\u092a\u093f\u0928\u0915\u094b\u0921 \u092d\u0947\u091c\u0947\u0902\n\u0909\u0926\u093e\u0939\u0930\u0923: #641001",
        "TA": "\u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0bae\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0ba4\u0bcd\u0ba4\u0bc8 \u0baa\u0ba4\u0bbf\u0bb5\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd:\n#\u0baa\u0bbf\u0ba9\u0bcd\u0b95\u0bcb\u0b9f\u0bcd \u0b85\u0ba8\u0bcd\u0ba4\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd\n\u0b89\u0ba4\u0bbe\u0bb0\u0ba3\u0bae\u0bcd: #641001",
    },

    # After pincode registered
    "registered": {
        "EN": "Fasal-to-Faida\n{action}!\nDistrict: {district}, {state}\n\nSelect crop:\n{crop_menu}\n\nReply with number.",
        "HI": "Fasal-to-Faida\n{action}!\n\u091c\u093f\u0932\u093e: {district}, {state}\n\n\u092b\u0938\u0932 \u091a\u0941\u0928\u0947\u0902:\n{crop_menu}\n\n\u0928\u0902\u092c\u0930 \u092d\u0947\u091c\u0947\u0902\u0964",
        "TA": "Fasal-to-Faida\n{action}!\n\u0bae\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0bae\u0bcd: {district}, {state}\n\n\u0baa\u0baf\u0bbf\u0bb0\u0bcd \u0ba4\u0bc7\u0bb0\u0bcd\u0bb5\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd:\n{crop_menu}\n\n\u0b8e\u0ba3\u0bcd \u0b85\u0ba9\u0bcd\u0baa\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd.",
    },

    "registered_action": {
        "EN": {"new": "Registered", "update": "Updated"},
        "HI": {"new": "\u092a\u0902\u091c\u0940\u0915\u0943\u0924", "update": "\u0905\u092a\u0921\u0947\u091f \u0939\u0941\u0906"},
        "TA": {"new": "\u0baa\u0ba4\u0bbf\u0bb5\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f\u0ba4\u0bc1", "update": "\u0bae\u0bc7\u0bae\u0bcd\u0baa\u0b9f\u0bc1\u0ba4\u0bcd\u0ba4\u0baa\u0bcd\u0baa\u0b9f\u0bcd\u0b9f\u0ba4\u0bc1"},
    },

    # Pincode errors
    "bad_pincode": {
        "EN": "Invalid pincode.\nSend a valid 6-digit pincode.\nExample: #641001",
        "HI": "\u0905\u092e\u093e\u0928\u094d\u092f \u092a\u093f\u0928\u0915\u094b\u0921\u0964\n6 \u0905\u0902\u0915\u094b\u0902 \u0935\u093e\u0932\u093e \u092a\u093f\u0928\u0915\u094b\u0921 \u092d\u0947\u091c\u0947\u0902\u0964\n\u0909\u0926\u093e: #641001",
        "TA": "\u0ba4\u0bb5\u0bb1\u0bbe\u0ba9 \u0baa\u0bbf\u0ba9\u0bcd\u0b95\u0bcb\u0b9f\u0bcd.\n\u0b9a\u0bb0\u0bbf\u0baf\u0bbe\u0ba9 6 \u0b8e\u0ba3\u0bcd \u0baa\u0bbf\u0ba9\u0bcd\u0b95\u0bcb\u0b9f\u0bcd \u0b85\u0ba9\u0bcd\u0baa\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd.\n\u0b89\u0ba4\u0bbe: #641001",
    },

    # MENU / HELLO for registered user — main crop menu
    "main_menu": {
        "EN": "Fasal-to-Faida\nDistrict: {district}\n\nSelect crop:\n{crop_menu}\n\nSend #PINCODE to change district.",
        "HI": "Fasal-to-Faida\n\u091c\u093f\u0932\u093e: {district}\n\n\u092b\u0938\u0932 \u091a\u0941\u0928\u0947\u0902:\n{crop_menu}\n\n\u091c\u093f\u0932\u093e \u092c\u0926\u0932\u0928\u0947 \u0915\u0947 \u0932\u093f\u090f #\u092a\u093f\u0928\u0915\u094b\u0921 \u092d\u0947\u091c\u0947\u0902\u0964",
        "TA": "Fasal-to-Faida\n\u0bae\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0bae\u0bcd: {district}\n\n\u0baa\u0baf\u0bbf\u0bb0\u0bcd \u0ba4\u0bc7\u0bb0\u0bcd\u0bb5\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd:\n{crop_menu}\n\n\u0bae\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0ba4\u0bcd\u0ba4\u0bc8 \u0bae\u0bbe\u0bb1\u0bcd\u0bb1 #\u0baa\u0bbf\u0ba9\u0bcd\u0b95\u0bcb\u0b9f\u0bcd \u0b85\u0ba9\u0bcd\u0baa\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd.",
    },

    # Session step: crop confirmation + month prompt
    "crop_ok_ask_month": {
        "EN": "Crop: {crop} OK\n\nWhich month to sell?\nReply 1-12\n(1=Jan  6=Jun  12=Dec)\nBack: *",
        "HI": "\u092b\u0938\u0932: {crop} \u0920\u0940\u0915 \u0939\u0948\n\n\u0915\u093f\u0938 \u092e\u0939\u0940\u0928\u0947 \u092c\u0947\u091a\u0928\u093e \u0939\u0948?\n1-12 \u0928\u0902\u092c\u0930 \u092d\u0947\u091c\u0947\u0902\n(1=\u091c\u0928  6=\u091c\u0942\u0928  12=\u0926\u093f\u0938)\n\u0935\u093e\u092a\u0938: *",
        "TA": "\u0baa\u0baf\u0bbf\u0bb0\u0bcd: {crop} \u0bb5\u0bbf\u0b9f\u0bc1\u0b95\u0bbf\u0bb1\u0bc7\u0ba9\u0bcd\n\n\u0b8e\u0ba4\u0bc1 \u0bae\u0bbe\u0ba4\u0ba4\u0bcd\u0ba4\u0bbf\u0bb2\u0bcd \u0bb5\u0bbf\u0bb1\u0bcd\u0b95\u0baa\u0bcd\u0baa\u0bcb\u0b95\u0bbf\u0bb1\u0bc0\u0bb0\u0bcd\u0b95\u0bb3\u0bcd?\n1-12 \u0b85\u0ba9\u0bcd\u0baa\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd\n(1=\u0b9c\u0ba9  6=\u0b9c\u0bc2\u0ba9\u0bcd  12=\u0b9f\u0bbf\u0b9a\u0bcd)\n\u0bae\u0bc1\u0ba8\u0bcd\u0ba4\u0bc8\u0baf \u0baa\u0b95\u0bcd\u0b95\u0bae\u0bcd: *",
    },

    # Session step: month confirmation + qty prompt
    "month_ok_ask_qty": {
        "EN": "Month: {month} OK\n\nSelect quantity:\n1. Below 500 kg\n2. 500-1000 kg\n3. 1000-5000 kg\n4. Above 5000 kg\nBack: *",
        "HI": "\u092e\u0939\u0940\u0928\u093e: {month} \u0920\u0940\u0915 \u0939\u0948\n\n\u092e\u093e\u0924\u094d\u0930\u093e \u091a\u0941\u0928\u0947\u0902:\n1. 500 \u0915\u093f\u0932\u094b \u0938\u0947 \u0915\u092e\n2. 500-1000 \u0915\u093f\u0932\u094b\n3. 1000-5000 \u0915\u093f\u0932\u094b\n4. 5000 \u0915\u093f\u0932\u094b \u0938\u0947 \u091c\u093c\u094d\u092f\u093e\u0926\u093e\n\u0935\u093e\u092a\u0938: *",
        "TA": "\u0bae\u0bbe\u0ba4\u0bae\u0bcd: {month} \u0b9a\u0bb0\u0bbf\n\n\u0b85\u0bb3\u0bb5\u0bc1 \u0ba4\u0bc7\u0bb0\u0bcd\u0bb5\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd:\n1. 500 \u0b95\u0bbf\u0bb2\u0bcb\u0bb5\u0bbf\u0bb0\u0bcd\u0b95\u0bcd\u0b95\u0bc1 \u0b95\u0bc1\u0bb1\u0bc8\u0bb5\u0bbe\u0b95\n2. 500-1000 \u0b95\u0bbf\u0bb2\u0bcb\n3. 1000-5000 \u0b95\u0bbf\u0bb2\u0bcb\n4. 5000 \u0b95\u0bbf\u0bb2\u0bcb\u0bb5\u0bbf\u0bb0\u0bcd\u0b95\u0bcd\u0b95\u0bc1 \u0bae\u0bc7\u0bb2\u0bcd\n\u0bae\u0bc1\u0ba8\u0bcd\u0ba4\u0bc8\u0baf \u0baa\u0b95\u0bcd\u0b95\u0bae\u0bcd: *",
    },

    # Invalid crop reply
    "invalid_crop": {
        "EN": "Reply {valid} for crop:\n{menu}",
        "HI": "फसल के लिए {valid} भेजें:\n{menu}",
        "TA": "\u0baa\u0baf\u0bbf\u0bb0\u0bc1\u0b95\u0bcd\u0b95\u0bc1 {valid} \u0b85\u0ba9\u0bcd\u0baa\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd:\n{menu}",
    },

    # Invalid month
    "invalid_month": {
        "EN": "Reply with month 1-12.\nExample: 3 for March.",
        "HI": "\u092e\u0939\u0940\u0928\u093e 1-12 \u092d\u0947\u091c\u0947\u0902\u0964\n\u0909\u0926\u093e: 3 \u092e\u093e\u0930\u094d\u091a \u0915\u0947 \u0932\u093f\u090f\u0964",
        "TA": "\u0bae\u0bbe\u0ba4\u0ba4\u0bcd\u0ba4\u0bbf\u0bb1\u0bcd\u0b95\u0bc1 1-12 \u0b85\u0ba9\u0bcd\u0baa\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd.\n\u0b89\u0ba4\u0bbe: 3 \u0bae\u0bbe\u0bb0\u0bcd\u0b9a\u0bcd.",
    },

    # Invalid qty
    "invalid_qty": {
        "EN": "Reply 1-4:\n1.<500kg   2.500-1000kg\n3.1-5 ton  4.>5000kg",
        "HI": "1-4 \u092d\u0947\u091c\u0947\u0902:\n1.<500\u0915\u093f  2.500-1000\u0915\u093f\n3.1-5\u091f\u0928  4.>5000\u0915\u093f",
        "TA": "1-4 \u0b85\u0ba9\u0bcd\u0baa\u0bc1\u0b999\u0bcd\u0b95\u0bb3\u0bcd:\n1.<500\u0b95\u0bbf  2.500-1000\u0b95\u0bbf\n3.1-5\u0b9f\u0ba9\u0bcd  4.>5000\u0b95\u0bbf",
    },

    # No results
    "no_results": {
        "EN": "No markets found for {crop}\nnear {district} in {month}.\n\nTry a different crop or month.\nMENU to start again.",
        "HI": "{district} \u0915\u0947 \u092a\u093e\u0938 {crop} \u0915\u0947 \u0932\u093f\u090f\n{month} \u092e\u0947\u0902 \u0915\u094b\u0908 \u092e\u0902\u0921\u0940 \u0928\u0939\u0940\u0902 \u092e\u093f\u0932\u0940\u0964\n\u0926\u0942\u0938\u0930\u0940 \u092b\u0938\u0932 \u092f\u093e \u092e\u0939\u0940\u0928\u093e \u0906\u091c\u093c\u092e\u093e\u090f\u0902\u0964\nMENU \u092d\u0947\u091c\u0947\u0902\u0964",
        "TA": "{district} \u0b85\u0bb0\u0bc1\u0b95\u0bbf\u0bb2\u0bcd {crop} \u0b95\u0bcd\u0b95\u0bbe\u0ba9\n{month} \u0bae\u0bbe\u0ba4\u0ba4\u0bcd\u0ba4\u0bbf\u0bb2\u0bcd \u0b9a\u0ba8\u0bcd\u0ba4\u0bc8 \u0b95\u0bbf\u0b9f\u0bc8\u0b95\u0bcd\u0b95\u0bb5\u0bbf\u0bb2\u0bcd\u0bb2\u0bc8.\n\u0bb5\u0bc7\u0bb1\u0bc1 \u0baa\u0baf\u0bbf\u0bb0\u0bcd \u0bae\u0bb1\u0bcd\u0bb1\u0bc1\u0bae\u0bcd \u0bae\u0bbe\u0ba4\u0ba4\u0bcd\u0ba4\u0bc8 \u0bae\u0bbe\u0bb1\u0bcd\u0bb1\u0bbf \u0baa\u0bbe\u0bb0\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd.\nMENU \u0b85\u0ba9\u0bcd\u0baa\u0bc1\u0b999\u0bcd\u0b95\u0bb3\u0bcd.",
    },

    # Result header
    "result_header": {
        "EN": "Top markets for {crop}\n({month}, {qty}kg from {district}):\n\n",
        "HI": "{crop} \u0915\u0947 \u0932\u093f\u090f \u0936\u0940\u0930\u094d\u0937 \u092e\u0902\u0921\u093f\u092f\u093e\u0902\n({month}, {qty}\u0915\u093f\u0932\u094b, {district}):\n\n",
        "TA": "{crop} \u0b95\u0bcd\u0b95\u0bbe\u0ba9 \u0b9a\u0bbf\u0bb1\u0ba8\u0bcd\u0ba4 \u0b9a\u0ba8\u0bcd\u0ba4\u0bc8\u0b95\u0bb3\u0bcd\n({month}, {qty}\u0b95\u0bbf\u0bb2\u0bcb, {district}):\n\n",
    },

    # Each market result line
    "result_item": {
        "EN": "{rank}. {market} ({dist}km)\n   Price: Rs.{price}/qtl\n   Net profit: Rs.{profit}\n\n",
        "HI": "{rank}. {market} ({dist}\u0915\u093f\u092e\u0940)\n   \u092d\u093e\u0935: \u0930\u0942{price}/\u0915\u094d\u0935\u093f\n   \u0936\u0941\u0926\u094d\u0927 \u0932\u093e\u092d: \u0930\u0942{profit}\n\n",
        "TA": "{rank}. {market} ({dist}\u0b95\u0bbf\u0bae\u0bc0)\n   \u0bb5\u0bbf\u0bb2\u0bc8: \u0bb0\u0bc2.{price}/\u0b95\u0bcd\u0bb5\u0bbf\n   \u0ba8\u0bbf\u0b95\u0bb0 \u0bb2\u0bbe\u0baa\u0bae\u0bcd: \u0bb0\u0bc2.{profit}\n\n",
    },

    # HELP message
    "help": {
        "EN": (
            "Fasal-to-Faida Help\n\n"
            "Register district:\n"
            "  #PINCODE (e.g. #641001)\n\n"
            "Get prediction:\n"
            "  Just text us\n\n"
            "Go back one step:\n"
            "  Send  *\n\n"
            "Change language:\n"
            "  LANG 1 / LANG 2 / LANG 3\n\n"
            "Restart: MENU or HI"
        ),
        "HI": (
            "Fasal-to-Faida \u0938\u0939\u093e\u092f\u0924\u093e\n\n"
            "\u091c\u093f\u0932\u093e \u0926\u0930\u094d\u091c \u0915\u0930\u0947\u0902:\n"
            "  #\u092a\u093f\u0928\u0915\u094b\u0921 (\u091c\u0948\u0938\u0947 #641001)\n\n"
            "\u092d\u093e\u0937\u093e \u092c\u0926\u0932\u0947\u0902:\n"
            "  LANG 1 / LANG 2 / LANG 3\n\n"
            "\u0935\u093e\u092a\u0938: *  |  \u0930\u093f\u0938\u0947\u091f: MENU"
        ),
        "TA": (
            "Fasal-to-Faida \u0b89\u0ba4\u0bb5\u0bbf\n\n"
            "\u0bae\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0bae\u0bcd \u0baa\u0ba4\u0bbf\u0bb5\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0baf:\n"
            "  #\u0baa\u0bbf\u0ba9\u0bcd\u0b95\u0bcb\u0b9f\u0bcd (\u0b89\u0ba4\u0bbe: #641001)\n\n"
            "\u0bae\u0bca\u0bb4\u0bbf \u0bae\u0bbe\u0bb1\u0bcd\u0bb1:\n"
            "  LANG 1 / LANG 2 / LANG 3\n\n"
            "\u0bae\u0bc1\u0ba8\u0bcd\u0ba4\u0bc8\u0baf: *  |  \u0bae\u0bb1\u0bc1\u0ba4\u0bc6\u0bbe\u0b9f\u0b95\u0bcd\u0b95\u0bae\u0bcd: MENU"
        ),
    },

    # Welcome for brand new user (shown before MENU after lang is chosen)
    "welcome_register": {
        "EN": "Welcome to Fasal-to-Faida!\n\nRegister your district:\nSend #PINCODE\nExample: #641001\n\nSend HELP for info.",
        "HI": "Fasal-to-Faida \u092e\u0947\u0902 \u0906\u092a\u0915\u093e \u0938\u094d\u0935\u093e\u0917\u0924 \u0939\u0948!\n\n\u0905\u092a\u0928\u093e \u091c\u093f\u0932\u093e \u0926\u0930\u094d\u091c \u0915\u0930\u0947\u0902:\n#\u092a\u093f\u0928\u0915\u094b\u0921 \u092d\u0947\u091c\u0947\u0902\n\u0909\u0926\u093e: #641001",
        "TA": "Fasal-to-Faida-\u0b95\u0bcd\u0b95\u0bc1 \u0bb5\u0bb0\u0bc1\u0b95!\n\n\u0b89\u0b99\u0bcd\u0b95\u0bb3\u0bcd \u0bae\u0bbe\u0bb5\u0b9f\u0bcd\u0b9f\u0ba4\u0bcd\u0ba4\u0bc8 \u0baa\u0ba4\u0bbf\u0bb5\u0bc1 \u0b9a\u0bc6\u0baf\u0bcd\u0baf\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd:\n#\u0baa\u0bbf\u0ba9\u0bcd\u0b95\u0bcb\u0b9f\u0bcd \u0b85\u0ba8\u0bcd\u0ba4\u0bc1\u0b99\u0bcd\u0b95\u0bb3\u0bcd\n\u0b89\u0ba4\u0bbe: #641001",
    },
}


def t(key: str, lang: str, **kwargs) -> str:
    """
    Translate key to lang, falling back to EN.
    Supports named {placeholders} via kwargs.
    """
    entry = STRINGS.get(key, {})
    text  = entry.get(lang) or entry.get("EN", f"[{key}]")
    return text.format(**kwargs) if kwargs else text


def crop_name(crop: str, lang: str) -> str:
    """Return crop display name in the given language."""
    return CROP_NAMES.get(crop, {}).get(lang, crop)
