# LapSim-AI browser MVP

Client-only TypeScript / Vite / Three.js / MediaPipe. No Python or Blender is
required by the built website. The native implementation remains the reference.

The public default is now [Beginner Free Transfer](../docs/web-beginner-polish.md):
two active minutes, any ring onto any target, automatic safe recycling and practice
results. Structured six-ring logic is preserved internally.

See [the implementation report and manual acceptance procedure](../docs/web-mvp.md)
and [the architecture decision](../docs/web-architecture.md).

With Node >=22.12 and pnpm 11.19.0 installed, from this directory:

```powershell
pnpm install --frozen-lockfile
pnpm dev
```

Open http://127.0.0.1:5173. Camera access begins only after Start training.
The build copies the existing checksum-verified model from the parent repository;
keep `assets/third_party/mediapipe_hand_landmarker` available when building.

```powershell
pnpm test
pnpm typecheck
pnpm build
pnpm preview
```

Preview is http://127.0.0.1:4173. Serve the complete `dist` folder over HTTPS in
production. No deployment has been performed in Phase 6. The maintainer reports a positive physical browser usability impression; detailed device/protocol evidence remains pending. See [current release evidence](../docs/release_evidence_v0.1.0.md).

The research-interest link defaults to the provided Google Form. To override it,
copy `.env.example` to `.env`, set
`VITE_RESEARCH_INTEREST_URL` to the final HTTPS URL, and rebuild. An empty or
invalid value explicitly disables the link. An unset variable uses the default.
Never place secrets in VITE
variables: they are public build-time configuration.

## Worker network containment

MediaPipe 1.0.1 internal metrics collection remains present. The worker response CSP blocks its external metrics connection. `vercel.json` applies the policy to `/assets/:path*`; Vite development/preview reads the same policy value. Use Vercel Root Directory `web`, build `pnpm build`, output `dist`, with parent model assets available during the build. An arbitrary static server does not automatically apply these headers. See [configuration and mandatory post-deployment checks](../docs/worker_network_containment.md). Local containment is verified; no Vercel deployment has been performed.
