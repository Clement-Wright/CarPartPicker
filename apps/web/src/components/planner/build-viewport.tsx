"use client";

import { OrbitControls, useGLTF } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Suspense } from "react";
import * as THREE from "three";

import type { V1BuildSceneResponse, V1ProxyGeometry } from "@/lib/types";

type Props = {
  scene?: V1BuildSceneResponse;
  loading?: boolean;
};

function assetLabel(mode: "exact_mesh_ready" | "proxy_from_dimensions" | "catalog_only" | "unsupported") {
  if (mode === "exact_mesh_ready") {
    return "3D";
  }
  if (mode === "proxy_from_dimensions") {
    return "Proxy";
  }
  return "Specs only";
}

function ExactMeshObject({
  meshUrl,
  position,
  rotation,
  scale
}: {
  meshUrl: string;
  position: [number, number, number];
  rotation: [number, number, number];
  scale: [number, number, number];
}) {
  const gltf = useGLTF(meshUrl);
  return <primitive object={gltf.scene.clone()} position={position} rotation={rotation} scale={scale} />;
}

function ProxyObject({
  geometry,
  position,
  rotation,
  scale
}: {
  geometry: V1ProxyGeometry;
  position: [number, number, number];
  rotation: [number, number, number];
  scale: [number, number, number];
}) {
  const color = new THREE.Color(geometry.color);

  if (geometry.kind === "cylinder") {
    return (
      <mesh position={position} rotation={[rotation[0] + Math.PI / 2, rotation[1], rotation[2]]} scale={scale}>
        <cylinderGeometry
          args={[
            Math.max((geometry.radius_mm ?? 160) / 1000, 0.08),
            Math.max((geometry.radius_mm ?? 160) / 1000, 0.08),
            Math.max((geometry.width_mm ?? geometry.length_mm ?? 220) / 1000, 0.04),
            32
          ]}
        />
        <meshStandardMaterial color={color} metalness={0.45} roughness={0.38} />
      </mesh>
    );
  }

  if (geometry.kind === "disc") {
    return (
      <mesh position={position} rotation={[rotation[0] + Math.PI / 2, rotation[1], rotation[2]]} scale={scale}>
        <cylinderGeometry
          args={[
            Math.max((geometry.radius_mm ?? 160) / 1000, 0.08),
            Math.max((geometry.radius_mm ?? 160) / 1000, 0.08),
            Math.max((geometry.thickness_mm ?? 32) / 1000, 0.015),
            28
          ]}
        />
        <meshStandardMaterial color={color} metalness={0.55} roughness={0.28} />
      </mesh>
    );
  }

  const size = geometry.size_mm ?? [500, 300, 300];
  return (
    <mesh position={position} rotation={rotation} scale={scale}>
      <boxGeometry args={[Math.max(size[0] / 1000, 0.1), Math.max(size[1] / 1000, 0.06), Math.max(size[2] / 1000, 0.06)]} />
      <meshStandardMaterial color={color} metalness={0.32} roughness={0.46} />
    </mesh>
  );
}

function SceneObject({
  item
}: {
  item: V1BuildSceneResponse["items"][number];
}) {
  if (item.asset_mode === "exact_mesh_ready" && item.mesh_url) {
    return (
      <ExactMeshObject
        meshUrl={item.mesh_url}
        position={item.transform.position}
        rotation={item.transform.rotation}
        scale={item.transform.scale}
      />
    );
  }

  if (item.proxy_geometry) {
    return (
      <ProxyObject
        geometry={item.proxy_geometry}
        position={item.transform.position}
        rotation={item.transform.rotation}
        scale={item.transform.scale}
      />
    );
  }

  return null;
}

export function BuildViewport({ scene, loading }: Props) {
  const hasRenderableItems = Boolean(scene?.items.length);

  return (
    <section className="panel rounded-[28px] p-4 lg:p-5">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">
            Visual Layer
          </p>
          <h2 className="mt-1 font-display text-3xl text-white">Build View</h2>
        </div>
        <div className="grid grid-cols-2 gap-2 rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-right">
          <div>
            <p className="font-display text-[11px] uppercase tracking-[0.2em] text-slate-400">
              Renderable
            </p>
            <p className="mt-1 font-display text-lg text-white">{scene?.summary.renderable_count ?? 0}</p>
          </div>
          <div>
            <p className="font-display text-[11px] uppercase tracking-[0.2em] text-slate-400">
              Omitted
            </p>
            <p className="mt-1 font-display text-lg text-white">{scene?.summary.omitted_count ?? 0}</p>
          </div>
        </div>
      </div>

      <div className="relative h-[420px] overflow-hidden rounded-[24px] border border-white/6 bg-[radial-gradient(circle_at_top,#1f2a33,transparent_32%),linear-gradient(180deg,#0b1015,#05080c)]">
        {loading ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">
            Updating scene coverage...
          </div>
        ) : (
          <>
            <Canvas camera={{ position: [4.8, 2.6, 4.8], fov: 35 }}>
              <color attach="background" args={["#05080c"]} />
              <ambientLight intensity={1.1} />
              <directionalLight position={[4, 6, 2]} intensity={1.8} color="#ffffff" />
              <directionalLight position={[-4, 3, -3]} intensity={0.6} color="#ffb36b" />
              <Suspense fallback={null}>
                <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.68, 0]}>
                  <planeGeometry args={[14, 14]} />
                  <meshStandardMaterial color="#0b1117" metalness={0.25} roughness={0.78} />
                </mesh>
                <gridHelper args={[14, 18, "#ff7b31", "#22303a"]} position={[0, -0.675, 0]} />
                {scene?.items.map((item) => (
                  <SceneObject key={item.instance_id} item={item} />
                ))}
              </Suspense>
              <OrbitControls enablePan={false} maxPolarAngle={Math.PI / 2.1} minDistance={3.5} maxDistance={8} />
            </Canvas>
            {!hasRenderableItems ? (
              <div className="pointer-events-none absolute inset-0 flex items-center justify-center px-6">
                <div className="max-w-lg rounded-[24px] border border-white/10 bg-black/55 px-5 py-4 text-center backdrop-blur">
                  <p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">3D Is Optional</p>
                  <p className="mt-2 text-sm leading-6 text-slate-200">
                    This build is still valid for fitment, pricing, specs, and simulation. The current selections are mostly
                    <span className="mx-1 rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-xs text-slate-200">Specs only</span>
                    items, so nothing meaningful is being rendered right now.
                  </p>
                </div>
              </div>
            ) : null}
          </>
        )}
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {scene?.highlights.length ? (
          scene.highlights.map((highlight) => (
            <div
              key={`${highlight.zone}-${highlight.message}`}
              className={`rounded-2xl border px-3 py-2 text-sm ${
                highlight.severity === "error"
                  ? "border-red-300/25 bg-red-300/10 text-red-100"
                  : "border-amber-300/20 bg-amber-300/10 text-amber-100"
              }`}
            >
              <span className="font-display uppercase tracking-[0.18em]">{highlight.zone}</span>
              <p className="mt-1 text-sm normal-case">{highlight.message}</p>
            </div>
          ))
        ) : (
          <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3 text-sm text-slate-400">
            Compatibility and clearance overlays will appear here when the current build needs attention.
          </div>
        )}

        <div className="rounded-2xl border border-white/8 bg-white/[0.03] px-4 py-3">
          <div className="flex items-center justify-between">
            <p className="font-display text-xs uppercase tracking-[0.2em] text-slate-400">Scene Coverage</p>
            <div className="flex gap-2 text-[10px] uppercase tracking-[0.18em] text-slate-300">
              <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">3D {scene?.summary.exact_count ?? 0}</span>
              <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">Proxy {scene?.summary.proxy_count ?? 0}</span>
              <span className="rounded-full border border-white/10 bg-white/5 px-2 py-1">Specs only {scene?.summary.omitted_count ?? 0}</span>
            </div>
          </div>
          {scene?.omitted_items.length ? (
            <div className="mt-3 space-y-2">
              {scene.omitted_items.slice(0, 4).map((item) => (
                <div
                  key={`${item.subsystem}-${item.part_id}`}
                  className="rounded-2xl border border-white/8 bg-black/10 px-3 py-2 text-sm text-slate-300"
                >
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-display text-[11px] uppercase tracking-[0.18em] text-slate-400">
                      {item.subsystem.replace(/_/g, " ")}
                    </span>
                    <span className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 text-[10px] uppercase tracking-[0.16em] text-slate-200">
                      {assetLabel(item.asset_mode)}
                    </span>
                  </div>
                  <p className="mt-1 text-xs leading-5 text-slate-400">{item.hidden_reason}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="mt-3 text-sm text-slate-400">
              Every currently selected item has some visual representation in the scene.
            </p>
          )}
        </div>
      </div>
    </section>
  );
}
