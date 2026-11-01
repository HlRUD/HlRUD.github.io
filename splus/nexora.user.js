
// ==UserScript==
// @name         NEXORA
// @namespace    https://github.com/HlRUD/HlRUD.github.io
// @version      1.0.0
// @description  Replace Soroush branding with NEXORA
// @match        https://web.splus.ir/*
// @run-at       document-idle
// @grant        none
// ==/UserScript==

(() => {
    "use strict";

    const replacements = [
        [/soroush\s*\+/gi, "NEXORA"],
        [/soroush\s*plus/gi, "NEXORA"],
        [/soroushplus/gi, "NEXORA"],
        [/soroush/gi, "NEXORA"],
        [/سروش\s*\+/g, "NEXORA"],
        [/سروش\s*پلاس/g, "NEXORA"],
        [/سروش/g, "NEXORA"]
    ];

    function replaceText(text) {
        let result = text;

        for (const [pattern, replacement] of replacements) {
            result = result.replace(pattern, replacement);
        }

        return result;
    }

    function scan(root) {
        if (!root) return;

        const walker = document.createTreeWalker(
            root,
            NodeFilter.SHOW_TEXT
        );

        let node;

        while ((node = walker.nextNode())) {
            if (node.nodeValue && /soroush|سروش/i.test(node.nodeValue)) {
                node.nodeValue = replaceText(node.nodeValue);
            }
        }

        if (root.querySelectorAll) {
            root.querySelectorAll(
                "[placeholder], [aria-label], [title], img[alt]"
            ).forEach(element => {
                ["placeholder", "aria-label", "title", "alt"].forEach(attr => {
                    const value = element.getAttribute(attr);
                    if (value) {
                        element.setAttribute(attr, replaceText(value));
                    }
                });
            });
        }
    }

    function start() {
        scan(document.body);
        document.title = replaceText(document.title);

        const observer = new MutationObserver(mutations => {
            for (const mutation of mutations) {
                if (mutation.type === "characterData") {
                    const node = mutation.target;
                    if (/soroush|سروش/i.test(node.nodeValue)) {
                        node.nodeValue = replaceText(node.nodeValue);
                    }
                }

                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === Node.TEXT_NODE) {
                        if (/soroush|سروش/i.test(node.nodeValue)) {
                            node.nodeValue = replaceText(node.nodeValue);
                        }
                    } else if (node.nodeType === Node.ELEMENT_NODE) {
                        scan(node);
                    }
                });
            }

            document.title = replaceText(document.title);
        });

        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
    }

    if (document.body) {
        start();
    } else {
        document.addEventListener("DOMContentLoaded", start);
    }

    console.log("%c NEXORA ACTIVE ", 
        "background:#39ff57;color:#000;padding:8px;font-weight:bold;"
    );
})();
