---
id: a9c5dee2-1e5b-47dd-b2ab-639db6950950
title: Expand configuration validation and automatic repair in ot check
type: feature
status: triage
size: small
created_at: 2026-11-09T18:36:39.497473+00:00
author:
  name: Tom Hicks
  email: headhunter3@gmail.com
---

# Expand configuration validation and automatic repair in ot check

## Overview
Extend Validator.validate_configuration and Repairer.repair to validate ~/.ot/config.json, check configSchemaVersion compatibility across layers, warn on protected keys in global user config, and support fine-grained dotted protected key repair per ADR-0016 and ADR-0017.
