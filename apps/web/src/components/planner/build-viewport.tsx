"use client";

import { OrbitControls } from "@react-three/drei";
import { Canvas } from "@react-three/fiber";
import { Suspense } from "react";
import * as THREE from "three";

import type { RenderConfig } from "@/lib/types";

type Props = {
  renderConfig?: RenderConfig;
  loading?: boolean;
};

function meshForKind(kind: string) {
  if (kind.includes("wheel") || kind.includes("tire")) {
    return "wheel";
  }
  if (kind.includes("shell") || kind.includes("track_aero")) {
    return "shell";
  }
  if (kind.includes("brake")) {
    return "brake";
  }
  if (kind.includes("flat4") || kind.includes("swap") || kind.includes("turbo")) {
    return "engine";
  }
  if (kind.includes("intercooler")) {
    return "cooler";
  }
  return "box";
}

function SceneObject({
  item
}: {
  item: RenderConfig["scene_objects"][number];
}) {
  const color = new THREE.Color(item.color);
  const emissive =
    item.highlight === "error"
      ? new THREE.Color("#ff5722")
      : item.highlight === "warning"
        ? new THREE.Color("#ffb36b")
        : new THREE.Color("#000000");

  const meshKind = meshForKind(item.kind);
  const commonProps = {
    position: item.position,
    rotation: item.rotation,
    scale: item.scale
  } as const;

  if (meshKind === "wheel") {
    return (
      <mesh {...commonProps} rotation={[Math.PI / 2, 0, 0]}>
        <cylinderGeometry args={[0.34, 0.34, 0.22, 36]} />
        <meshStandardMaterial color={color} emissive={emissive} metalness={0.55} roughness={0.32} />
      </mesh>
    );
  }

  if (meshKind === "shell") {
    return (
      <mesh {...commonProps}>
        <boxGeometry args={[1.8, 0.42, 3.55]} />
        <meshStandardMaterial color={color} emissive={emissive} metalness={0.3} roughness={0.46} />
      </mesh>
    );
  }

  if (meshKind === "brake") {
    return (
      <mesh {...commonProps}>
        <cylinderGeometry args={[0.18, 0.18, 0.12, 20]} />
        <meshStandardMaterial color={color} emissive={emissive} metalness={0.48} roughness={0.36} />
      </mesh>
    );
  }

  if (meshKind === "engine") {
    return (
      <mesh {...commonProps}>
        <boxGeometry args={[0.85, 0.42, 0.7]} />
        <meshStandardMaterial color={color} emissive={emissive} metalness={0.55} roughness={0.34} />
      </mesh>
    );
  }

  if (meshKind === "cooler") {
    return (
      <mesh {...commonProps}>
        <boxGeometry args={[0.72, 0.16, 0.08]} />
        <meshStandardMaterial color={color} emissive={emissive} metalness={0.42} roughness={0.38} />
      </mesh>
    );
  }

  return (
    <mesh {...commonProps}>
      <boxGeometry args={[0.5, 0.3, 0.5]} />
      <meshStandardMaterial color={color} emissive={emissive} metalness={0.4} roughness={0.45} />
    </mesh>
  );
}

export function BuildViewport({ renderConfig, loading }: Props) {
  return (
    <section className="panel rounded-[28px] p-4 lg:p-5">
      <div className="mb-4 flex items-start justify-between gap-4">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.24em] text-slate-400">
            Assemble
          </p>
          <h2 className="mt-1 font-display text-3xl text-white">3D Build View</h2>
        </div>
        <div className="rounded-2xl border border-white/10 bg-white/5 px-3 py-2 text-right">
          <p className="font-display text-[11px] uppercase tracking-[0.2em] text-slate-400">
            Ride Drop
          </p>
          <p className="mt-1 font-display text-lg text-white">
            {renderConfig?.ride_height_drop_mm ?? 0}
            <span className="ml-1 text-sm text-slate-400">mm</span>
          </p>
        </div>
      </div>

      <div className="h-[420px] overflow-hidden rounded-[24px] border border-white/6 bg-[radial-gradient(circle_at_top,#1f2a33,transparent_32%),linear-gradient(180deg,#0b1015,#05080c)]">
        {loading ? (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">
            Updating assembled car scene...
          </div>
        ) : (
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
              {renderConfig?.scene_objects.map((item) => (
                <SceneObject key={item.object_id} item={item} />
              ))}
            </Suspense>
            <OrbitControls enablePan={false} maxPolarAngle={Math.PI / 2.1} minDistance={3.5} maxDistance={8} />
          </Canvas>
        )}
      </div>

      {renderConfig?.highlights?.length ? (
        <div className="mt-4 grid gap-2 md:grid-cols-2">
          {renderConfig.highlights.map((highlight) => (
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
          ))}
        </div>
      ) : (
        <p className="mt-4 text-sm text-slate-400">
          Clearance and fabrication overlays will appear here when the current build needs attention.
        </p>
      )}
    </section>
  );
}
