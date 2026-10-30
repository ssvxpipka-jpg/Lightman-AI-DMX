# Server OS

> **STUB — Future feature planned for Lightman 2.0**
> This document describes the planned Server OS. Implementation is deferred.

## Overview

The Lightman Server OS is a dedicated operating system image designed to run
the Lightman control server in a production theater environment. It will
provide:

- **Central Device Management**: Discover and register all Sound, Light, and
  Director apps on the network.
- **Hardware Abstraction Layer (HAL)**: Unified API for DMX, ArtNet, sACN,
  and proprietary console protocols.
- **Network-Wide Sync**: Sub-millisecond synchronization via PTP (Precision
  Time Protocol) for coordinated lighting across multiple rooms.
- **Failover & Redundancy**: Automatic failover if the primary Director goes
  offline.
- **Embedded Database**: SQLite-based show file and cue storage with
  automatic backups.
- **WebSocket Bridge**: Browser-based remote control interface.

## Architecture

```
┌──────────────────────────────────────────┐
│        Lightman Server OS                │
├──────────────────────────────────────────┤
│  Web UI  │  WebSocket API  │  REST API  │
├──────────────────────────────────────────┤
│  Multi-Agent Orchestrator (LangGraph)   │
├──────────────────────────────────────────┤
│  HAL: DMX  ArtNet  sACN  Console APIs   │
├──────────────────────────────────────────┤
│  Linux Kernel (real-time patched)        │
└──────────────────────────────────────────┘
```

## Future Components

- `server_os/core.py`: Server bootstrap and agent orchestration.
- `server_os/hal/`: Hardware abstraction layer modules.
- `server_os/discovery.py`: Network device discovery via mDNS/Zeroconf.
- `server_os/sync.py`: PTP-based time synchronization.
- `server_os/web/`: Embedded web server for remote control.

## Timeline

Planned for Lightman 2.0 (post-1.1). Not implemented in the current alpha.
