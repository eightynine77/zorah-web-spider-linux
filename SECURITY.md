# Security & Responsible Disclosure

This project (Zorah Web Spider) is provided for defensive security testing, research, and education **only**.
Please use it only on systems you own or systems for which you have explicit written permission.

## Reporting security issues
If you discover a vulnerability in this project, please **do not** post a public proof-of-concept. Instead either:
- Open a **private** GitHub issue and add the label `security`, or
- Email: <june-jacob@example.com> (replace with a monitored address).

When reporting, include:
- A short description of the issue and affected version (commit/branch).
- Steps to reproduce and a minimal test case (if possible).
- Contact information and a preferred disclosure timeline.

We will respond in a reasonable timeframe and coordinate disclosure.

## Project security posture
- This project is a **local GUI** wrapper that calls user-supplied CLI tools. We do **not** ship or download pentest binaries.
- The project defaults to `localhost` bindings only (no public service).
- We **do not** accept or merge code that adds automatic exploitation, hosting, mass-scanning, or remote orchestration features.

Do not use this software to perform unauthorized scanning or attacks. Use responsibly.
