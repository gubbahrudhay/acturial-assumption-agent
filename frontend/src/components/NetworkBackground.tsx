"use client"

import { useRef, useMemo } from 'react'
import { Canvas, useFrame, useThree } from '@react-three/fiber'
import * as THREE from 'three'

const PARTICLE_COUNT = 150
const MAX_DISTANCE = 2.0

const Particles = () => {
  const pointsRef = useRef<THREE.Points>(null)
  const linesRef = useRef<THREE.LineSegments>(null)
  const { mouse, viewport } = useThree()
  
  // Initialize particle positions and velocities
  const [positions, velocities] = useMemo(() => {
    const pos = new Float32Array(PARTICLE_COUNT * 3)
    const vel = []
    
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      pos[i * 3] = (Math.random() - 0.5) * 15
      pos[i * 3 + 1] = (Math.random() - 0.5) * 15
      pos[i * 3 + 2] = (Math.random() - 0.5) * 5
      
      vel.push({
        x: (Math.random() - 0.5) * 0.02,
        y: (Math.random() - 0.5) * 0.02,
        z: (Math.random() - 0.5) * 0.02
      })
    }
    return [pos, vel]
  }, [])
  
  // Animation Loop
  useFrame(() => {
    if (!pointsRef.current || !linesRef.current) return
    
    const positions = pointsRef.current.geometry.attributes.position.array as Float32Array
    
    // Convert mouse to world coordinates roughly
    const mouseX = (mouse.x * viewport.width) / 2
    const mouseY = (mouse.y * viewport.height) / 2
    
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      positions[i * 3] += velocities[i].x
      positions[i * 3 + 1] += velocities[i].y
      positions[i * 3 + 2] += velocities[i].z
      
      // Bounds check
      if (Math.abs(positions[i * 3]) > 10) velocities[i].x *= -1
      if (Math.abs(positions[i * 3 + 1]) > 10) velocities[i].y *= -1
      if (Math.abs(positions[i * 3 + 2]) > 5) velocities[i].z *= -1
    }
    
    pointsRef.current.geometry.attributes.position.needsUpdate = true
    
    // Draw lines between close particles and the mouse
    const linePositions = []
    const lineColors = []
    
    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const x1 = positions[i * 3]
      const y1 = positions[i * 3 + 1]
      const z1 = positions[i * 3 + 2]
      
      // Connect to mouse if close
      const distToMouse = Math.sqrt(Math.pow(x1 - mouseX, 2) + Math.pow(y1 - mouseY, 2))
      if (distToMouse < 3.0) {
         linePositions.push(x1, y1, z1)
         linePositions.push(mouseX, mouseY, 0)
         lineColors.push(1, 0.22, 0.36, 1 - (distToMouse/3.0)) // #ff385c
         lineColors.push(1, 0.22, 0.36, 1 - (distToMouse/3.0))
      }
      
      // Connect to other particles
      for (let j = i + 1; j < PARTICLE_COUNT; j++) {
        const x2 = positions[j * 3]
        const y2 = positions[j * 3 + 1]
        const z2 = positions[j * 3 + 2]
        
        const dist = Math.sqrt(Math.pow(x1 - x2, 2) + Math.pow(y1 - y2, 2) + Math.pow(z1 - z2, 2))
        
        if (dist < MAX_DISTANCE) {
          const alpha = 1.0 - (dist / MAX_DISTANCE)
          linePositions.push(x1, y1, z1)
          linePositions.push(x2, y2, z2)
          lineColors.push(0.8, 0.8, 0.8, alpha * 0.3) 
          lineColors.push(0.8, 0.8, 0.8, alpha * 0.3)
        }
      }
    }
    
    linesRef.current.geometry.setAttribute('position', new THREE.Float32BufferAttribute(linePositions, 3))
    linesRef.current.geometry.setAttribute('color', new THREE.Float32BufferAttribute(lineColors, 4))
  })
  
  return (
    <>
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute attach="attributes-position" array={positions} itemSize={3} count={PARTICLE_COUNT} />
        </bufferGeometry>
        <pointsMaterial size={0.05} color="#aaaaaa" transparent opacity={0.6} sizeAttenuation />
      </points>
      <lineSegments ref={linesRef}>
        <bufferGeometry />
        <lineBasicMaterial vertexColors transparent depthWrite={false} />
      </lineSegments>
    </>
  )
}

export default function NetworkBackground() {
  return (
    <div className="absolute inset-0 z-0 opacity-40 pointer-events-none">
      <Canvas camera={{ position: [0, 0, 10], fov: 60 }}>
        <Particles />
      </Canvas>
    </div>
  )
}
