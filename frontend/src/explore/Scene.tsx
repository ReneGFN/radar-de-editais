import { useEffect, useRef, useState } from 'react'
import * as THREE from 'three'
import { OrbitControls } from 'three/addons/controls/OrbitControls.js'
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js'
import type { DocumentSelection } from '../chat'
import type { ExploreEdital } from '../pages/ExplorePage'

type Props = { editais: ExploreEdital[]; selected: string; highlighted: string[]; onSelect: (id: string) => void; onDocument: (id: string, sequence: number) => void; onState: (uf: string) => void; onOverview: () => void; onPlaced: (id: string, sequence: number) => void; basket: DocumentSelection[]; documentSequence?: number }
const stateNames: Record<string, string> = { AM: 'Amazonas', BA: 'Bahia', CE: 'Ceará', DF: 'Distrito Federal', GO: 'Goiás', MG: 'Minas Gerais', MT: 'Mato Grosso', PA: 'Pará', PE: 'Pernambuco', PR: 'Paraná', RJ: 'Rio de Janeiro', RS: 'Rio Grande do Sul', SC: 'Santa Catarina', SP: 'São Paulo' }

type Actions = { syncBasket: (files: DocumentSelection[]) => void; zoom: (factor: number) => void; reset: () => void; focus: () => void; unfold: (open: boolean) => void; transport: (sequence?: number) => void }
type FileNode = { group: THREE.Group; rest: THREE.Vector3; sequence: number; index: number }
type Archive = { root: THREE.Group; files: FileNode[]; material: THREE.MeshStandardMaterial; rim: THREE.MeshStandardMaterial; size: number; open: boolean; changed: number; lift: number }

export default function Scene(props: Props) {
  const cameraPose = useRef<{position: THREE.Vector3; target: THREE.Vector3; zoom: number; span: number} | null>(null)
  const host = useRef<HTMLDivElement>(null)
  const latest = useRef(props); latest.current = props
  const actions = useRef<Actions | null>(null)
  const invalidate = useRef<() => void>(() => {})
  const [failed, setFailed] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [ready, setReady] = useState(false)
  const [status, setStatus] = useState('Segure e puxe um arquivo para explorar seus PDFs.')
  const labels = useRef(new Map<string, HTMLButtonElement>())
  const dropZone = useRef<HTMLDivElement>(null)
  const [dragFile, setDragFile] = useState<{sequence: number; x: number; y: number} | null>(null)
  const stateCounts = [...new Set(props.editais.map(e => e.uf ?? '—'))].sort().map(uf => ({uf, count: props.editais.filter(e => (e.uf ?? '—') === uf).length}))
  const selectedEdital = props.editais.find(e => e.pncp_id === props.selected)
  const selectedAvailable = props.editais.some(e => e.pncp_id === props.selected)
  const layout = props.editais.map(e => e.pncp_id).join('|')
  useEffect(() => {
    const element = host.current
    if (!element) return
    let renderer: THREE.WebGLRenderer
    try { renderer = new THREE.WebGLRenderer({ antialias: true }) } catch { setFailed(true); return }
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)')
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 1.5))
    renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap
    renderer.setClearColor('#0e1320'); renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.domElement.setAttribute('aria-label', 'Arquivo documental 3D; as mesmas ações estão disponíveis nos botões e na lista')
    renderer.domElement.setAttribute('role', 'img'); element.appendChild(renderer.domElement)
    const scene = new THREE.Scene()
    const camera = new THREE.OrthographicCamera(-20, 20, 14, -14, .1, 200)
    const states = [...new Set(latest.current.editais.map(e => e.uf ?? '—'))].sort()
    const columns = Math.min(4, states.length); const rows = Math.ceil(states.length / columns)
    const span = Math.max(columns * 8.5, rows * 8.5, 10)
    const home = new THREE.Vector3(span * .68, span * .78, span * .86)
    camera.position.copy(home)
    const controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = false; controls.minPolarAngle = .15; controls.maxPolarAngle = Math.PI / 2.15
    controls.minZoom = .45; controls.maxZoom = 5; controls.target.set(0, 0, 1)
    scene.add(new THREE.HemisphereLight('#cee6ff', '#25283b', 2.2))
    const sun = new THREE.DirectionalLight('#fff4e1', 3.5); sun.position.set(-12, 26, 12)
    sun.castShadow = true; sun.shadow.mapSize.set(1024, 1024)
    sun.shadow.camera.left = -span; sun.shadow.camera.right = span; sun.shadow.camera.top = span; sun.shadow.camera.bottom = -span
    sun.shadow.normalBias = .05; scene.add(sun)
    const blue = new THREE.PointLight('#73c9ff', 35, span); blue.position.set(10, 8, 0); scene.add(blue)
    const resources: (THREE.BufferGeometry | THREE.Material | THREE.Texture)[] = []
    const pickables: THREE.Object3D[] = []
    const districtPoints = new Map<string, THREE.Vector3>()
    const archives = new Map<string, Archive>()
    let frame = 0; let disposed = false; let cameraMotion: { start: number; from: THREE.Vector3; to: THREE.Vector3; targetFrom: THREE.Vector3; targetTo: THREE.Vector3; zoomFrom: number; zoomTo: number; duration: number } | null = null
    let travel: { start: number; curve: THREE.CatmullRomCurve3; group: THREE.Group; file: number; id: string; trail: THREE.Mesh } | null = null
    let inspection: THREE.Group | null = null
    let settling = 0; let hovering = ''
    const dock = new THREE.Vector3(0, .5, rows * 4.25 + 4.5)
    const station = new THREE.Group(); station.position.copy(dock); scene.add(station)
    function box(parent: THREE.Object3D, w: number, h: number, d: number, color: string, x: number, y: number, z: number, radius = .08) {
      const geometry = new RoundedBoxGeometry(w, h, d, 3, Math.min(radius, w / 3, h / 3, d / 3))
      const material = new THREE.MeshStandardMaterial({ color, roughness: .42, metalness: .22 })
      const mesh = new THREE.Mesh(geometry, material); mesh.position.set(x, y, z)
      mesh.castShadow = true; mesh.receiveShadow = true; parent.add(mesh); resources.push(geometry, material)
      return mesh
    }
    function textTexture(text: string, subtitle = '', color = '#c7deff') {
      const canvas = document.createElement('canvas'); canvas.width = 512; canvas.height = 256
      const ctx = canvas.getContext('2d')!
      ctx.fillStyle = '#17243c'; ctx.fillRect(0, 0, 512, 256)
      ctx.fillStyle = color; ctx.font = '600 100px sans-serif'; ctx.textAlign = 'center'; ctx.fillText(text, 256, 130, 470)
      ctx.fillStyle = '#9aafca'; ctx.font = '500 36px sans-serif'; ctx.fillText(subtitle, 256, 208, 470)
      const texture = new THREE.CanvasTexture(canvas); texture.colorSpace = THREE.SRGBColorSpace; resources.push(texture)
      return texture
    }
    function sign(parent: THREE.Object3D, text: string, sub: string, w: number, x: number, y: number, z: number) {
      const geo = new THREE.PlaneGeometry(w, w / 2)
      const material = new THREE.MeshBasicMaterial({ map: textTexture(text, sub), side: THREE.DoubleSide })
      const mesh = new THREE.Mesh(geo, material); mesh.rotation.x = -Math.PI / 2; mesh.position.set(x, y, z)
      parent.add(mesh); resources.push(geo, material)
    }
    function paper(parent: THREE.Object3D, size: number, sequence: number) {
      const group = new THREE.Group(); parent.add(group)
      box(group, size * .75, .055, size, '#e3eaf5', 0, 0, 0, .03)
      const canvas = document.createElement('canvas'); canvas.width = 256; canvas.height = 360
      const ctx = canvas.getContext('2d')!; ctx.fillStyle = '#e3eaf5'; ctx.fillRect(0, 0, 256, 360)
      ctx.fillStyle = '#345574'; ctx.font = '700 30px sans-serif'; ctx.fillText(`PDF ${sequence}`, 25, 55)
      ctx.fillStyle = '#8ca3bb'; for (let i = 0; i < 8; i++) ctx.fillRect(25, 92 + i * 26, i === 7 ? 112 : 205, 5)
      ctx.fillStyle = '#adcadf'; ctx.fillRect(25, 310, 55, 14)
      const texture = new THREE.CanvasTexture(canvas); texture.colorSpace = THREE.SRGBColorSpace
      const geo = new THREE.PlaneGeometry(size * .71, size * .95)
      const material = new THREE.MeshBasicMaterial({ map: texture, side: THREE.DoubleSide })
      const face = new THREE.Mesh(geo, material); face.rotation.x = -Math.PI / 2; face.position.y = .029; group.add(face)
      resources.push(texture, geo, material); return group
    }
    box(scene, span + 8, .2, span + 15, '#151d2b', 0, -.65, 2)
    box(station, 5, .28, 2.8, '#293d52', 0, 0, 0)
    box(station, 4.8, .04, 2.6, '#4c8299', 0, .18, 0)
    sign(station, 'FONTES', 'CONFERÊNCIA', 1.5, -1.6, .22, -.9)
    const deskFiles = new Map<string, THREE.Group>()
    function syncBasket(files: DocumentSelection[]) {
      if (inspection && !travel) { scene.remove(inspection); inspection=null }
      const keys = new Set(files.map(f => `${f.pncp_id}:${f.document_sequence}`))
      deskFiles.forEach((group,key) => { if (!keys.has(key)) { station.remove(group); group.traverse(object => { if (object instanceof THREE.Mesh) { const owned = [object.geometry, object.material, object.material.map].filter(Boolean); owned.forEach(resource => { resource.dispose(); const index = resources.indexOf(resource); if (index >= 0) resources.splice(index,1) }) } }); deskFiles.delete(key) } })
      files.forEach((file,index) => { const key = `${file.pncp_id}:${file.document_sequence}`; let group = deskFiles.get(key); if (!group) { group=paper(station,.95,file.document_sequence); deskFiles.set(key,group) }; group.position.set(-1.6+index*.8,.25+index*.018,.35) })
      request()
    }
    states.forEach((uf, index) => {
      const x = (index % columns - (columns - 1) / 2) * 8.5
      const z = (Math.floor(index / columns) - (rows - 1) / 2) * 8.5
      const district = new THREE.Group(); district.position.set(x, -.25, z); scene.add(district)
      const platform = box(district, 7.7, .35, 7.7, '#293448', 0, 0, 0, .16)
      platform.userData.uf = uf; pickables.push(platform)
      districtPoints.set(uf, new THREE.Vector3(x, .7, z - 2.5))
      box(district, 7.45, .04, 7.45, '#202b40', 0, .2, 0)
      sign(district, uf, `${latest.current.editais.filter(e => e.uf === uf).length} EDITAIS`, 2.2, -2.4, .23, -2.5)
      // Faixas de circulação: organização visual do catálogo, não localização geográfica.
      box(district, 6.6, .018, .035, '#65829c', 0, .235, 2.98)
      const group = latest.current.editais.filter(e => (e.uf ?? '—') === uf)
      const cols = Math.ceil(Math.sqrt(group.length)); const size = Math.min(1.65, 5.6 / cols)
      group.forEach((edital, i) => {
        const root = new THREE.Group()
        root.position.set(x + (i % cols - (cols - 1) / 2) * size * 1.25, 0, z + (Math.floor(i / cols) - (Math.ceil(group.length / cols) - 1) / 2) * size * 1.35 + .6)
        scene.add(root)
        const base = box(root, size * 1.07, .16, size * 1.18, '#466680', 0, .17, 0)
        const shell = box(root, size * .97, .38, size * 1.08, '#6581a9', 0, .4, 0)
        box(root, size * .42, .16, .15, '#9baecc', -size * .22, .64, -size * .52)
        const files = edital.documents.map((document, index) => {
          const file = paper(root, size * .82, document.sequence)
          const rest = new THREE.Vector3(0, .64 + index * .085, 0); file.position.copy(rest)
          file.rotation.y = (index % 2 ? 1 : -1) * .025
          file.traverse(object => { if (object instanceof THREE.Mesh) { object.userData.pncp = edital.pncp_id; object.userData.sequence = document.sequence; pickables.push(object) } })
          return { group: file, rest, sequence: document.sequence, index }
        })
        root.traverse(object => { if (object instanceof THREE.Mesh && !object.userData.pncp) { object.userData.pncp = edital.pncp_id; pickables.push(object) } })
        archives.set(edital.pncp_id, { root, files, material: shell.material, rim: base.material, size, open: false, changed: 0, lift: 0 })
      })
    })
    function render() {
      renderer.render(scene, camera)
      districtPoints.forEach((position, uf) => {
        const label = labels.current.get(uf); if (!label) return
        const projected = position.clone().project(camera)
        const x = (projected.x + 1) * element!.clientWidth / 2
        const y = (1 - projected.y) * element!.clientHeight / 2
        const compact = states.length > 1 && (camera.zoom < .7 || element!.clientWidth < 600)
        const labelIndex = states.indexOf(uf)
        const labelColumns = element!.clientWidth < 600 ? 3 : 4
        if (compact) {
          label.style.left = `${55 + (labelIndex % labelColumns) * (element!.clientWidth - 110) / (labelColumns - 1)}px`
          label.style.top = `${155 + Math.floor(labelIndex / labelColumns) * 38}px`
          label.style.visibility = 'visible'
          return
        }
        label.style.left = `${Math.max(55, Math.min(element!.clientWidth - 55, x))}px`
        label.style.top = `${Math.max(150, Math.min(element!.clientHeight - 130, y))}px`
        label.style.visibility = Math.abs(projected.x) <= 1.15 && Math.abs(projected.y) <= 1.15 ? 'visible' : 'hidden'
      })
    }
    function request() { if (!frame && !disposed && !document.hidden) frame = requestAnimationFrame(tick) }
    function tweenCamera(target: THREE.Vector3, zoom: number, duration = 650) {
      const offset = home.clone().normalize().multiplyScalar(span * 1.15)
      cameraMotion = { start: performance.now(), from: camera.position.clone(), to: target.clone().add(offset), targetFrom: controls.target.clone(), targetTo: target.clone(), zoomFrom: camera.zoom, zoomTo: zoom, duration }; request()
    }
    function openArchive(id: string, open: boolean) {
      const archive = archives.get(id); if (!archive) return
      archive.open = open; archive.changed = performance.now(); request()
    }
    function tick(now: number) {
      frame = 0; let active = false
      const dt = Math.min(.04, Math.max(.001, (now - settling) / 1000)); settling = now
      archives.forEach((archive, id) => {
        archive.root.position.y = THREE.MathUtils.lerp(archive.root.position.y, archive.lift, reduce.matches ? 1 : 1 - Math.exp(-dt * 10))
        if (Math.abs(archive.root.position.y - archive.lift) > .001) active = true
        archive.material.color.set(id === latest.current.selected ? '#55aac9' : id === hovering ? '#91aacf' : '#6581a9')
        archive.rim.color.set(latest.current.highlighted.includes(id) ? '#e5b66b' : '#466680')
        archive.material.emissive.set(id === hovering ? '#172438' : '#000000')
        archive.files.forEach(file => {
          const elapsed = now - archive.changed
          const delay = archive.open ? file.index * 65 : (archive.files.length - file.index - 1) * 95
          const isOpen = reduce.matches ? archive.open : archive.open ? elapsed >= delay : elapsed < delay
          const target = isOpen ? new THREE.Vector3((file.index - (archive.files.length - 1) / 2) * archive.size * .32, 2.4 + file.index * .22, -file.index * archive.size * .24) : file.rest
          const blend = reduce.matches ? 1 : 1 - Math.exp(-dt * (archive.open ? 9 : 12))
          file.group.position.lerp(target, blend)
          const rot = isOpen ? -.38 : 0
          file.group.rotation.x = THREE.MathUtils.lerp(file.group.rotation.x, rot, blend)
          file.group.rotation.z = THREE.MathUtils.lerp(file.group.rotation.z, isOpen ? (file.index - (archive.files.length - 1) / 2) * .12 : 0, blend)
          if (file.group.position.distanceToSquared(target) > .0001 || (!reduce.matches && elapsed < delay + 700)) active = true
        })
      })
      if (cameraMotion) {
        const t = reduce.matches ? 1 : Math.min(1, (now - cameraMotion.start) / cameraMotion.duration)
        const ease = t * t * (3 - 2 * t)
        camera.position.lerpVectors(cameraMotion.from, cameraMotion.to, ease); controls.target.lerpVectors(cameraMotion.targetFrom, cameraMotion.targetTo, ease)
        camera.zoom = THREE.MathUtils.lerp(cameraMotion.zoomFrom, cameraMotion.zoomTo, ease); camera.updateProjectionMatrix(); controls.update()
        if (t === 1) cameraMotion = null; else active = true
      }
      if (travel) {
        const t = reduce.matches ? 1 : Math.min(1, (now - travel.start) / 1500)
        const eased = t * t * (3 - 2 * t)
        travel.group.position.copy(travel.curve.getPoint(eased)); travel.group.rotation.set((1-eased) * -.38, Math.sin(t * Math.PI) * .35, 0)
        if (t === 1) { scene.remove(travel.trail); travel.trail.geometry.dispose(); (travel.trail.material as THREE.Material).dispose(); resources.splice(resources.indexOf(travel.trail.geometry), 1); resources.splice(resources.indexOf(travel.trail.material as THREE.Material), 1); setStatus(`PDF ${travel.file} na mesa. Confira o documento no painel.`); latest.current.onDocument(travel.id, travel.file); latest.current.onPlaced(travel.id, travel.file); travel = null }
        else active = true
      }
      render(); if (active) request()
    }
    invalidate.current = request
    function transport(sequence?: number) {
      const id = latest.current.selected; const archive = archives.get(id); if (!archive || travel) return
      const file = archive.files.find(f => f.sequence === sequence) ?? archive.files[0]; if (!file) return
      // Representa levar um documento à conferência; não indica processamento do backend.
      if (inspection) scene.remove(inspection)
      const moving = file.group.clone(true); moving.scale.setScalar(1.8 / (archive.size * .82)); scene.add(moving); inspection = moving
      moving.userData.transported = true
      const start = archive.root.localToWorld(file.group.position.clone())
      const finish = dock.clone().add(new THREE.Vector3(0, .24, 0))
      const curve = new THREE.CatmullRomCurve3([start, start.clone().add(new THREE.Vector3(0, 3, 0)), start.clone().lerp(finish, .6).add(new THREE.Vector3(0, 3, 0)), finish])
      const geometry = new THREE.TubeGeometry(curve, 50, .025, 5, false)
      const material = new THREE.MeshBasicMaterial({ color: '#79cad9', transparent: true, opacity: .55 })
      const trail = new THREE.Mesh(geometry, material); scene.add(trail); resources.push(geometry, material)
      moving.position.copy(start); travel = { start: performance.now(), curve, group: moving, file: file.sequence, id, trail }
      setStatus(`Levando PDF ${file.sequence} à mesa de conferência…`); tweenCamera(dock, Math.min(3.2, span / 10)); request()
    }
    const resize = () => {
      const width = element.clientWidth; const height = element.clientHeight; const half = span * .49
      camera.left = -half * width / Math.max(1, height); camera.right = -camera.left; camera.top = half; camera.bottom = -half
      camera.updateProjectionMatrix(); renderer.setSize(width, height); request()
    }
    const observer = new ResizeObserver(resize); observer.observe(element)
    controls.addEventListener('change', request)
    controls.addEventListener('start', () => { cameraMotion = null })
    controls.update(); controls.saveState()
    actions.current = {
      syncBasket,
      zoom: factor => { camera.zoom = Math.max(.45, Math.min(5, camera.zoom * factor)); camera.updateProjectionMatrix(); request() },
      reset: () => { archives.forEach((_, id) => openArchive(id, false)); setExpanded(false); tweenCamera(new THREE.Vector3(0, 0, 1), 1, 900) },
      focus: () => { const archive = archives.get(latest.current.selected); if (archive) tweenCamera(archive.root.position, Math.min(3.7, span / 9)) },
      unfold: open => { archives.forEach((_, id) => openArchive(id, open && id === latest.current.selected)); setExpanded(open); const archive = archives.get(latest.current.selected); if (open && archive) tweenCamera(archive.root.position.clone().add(new THREE.Vector3(0, 1, 0)), Math.min(4.4, span / 6)); setStatus(open ? 'Documentos abertos. Selecione um PDF no leque para conferir.' : 'PDFs recolhidos em sequência.') },
      transport,
    }
    const ray = new THREE.Raycaster(); const pointer = new THREE.Vector2()
    function hit(event: PointerEvent) {
      const rect = renderer.domElement.getBoundingClientRect()
      pointer.set((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1)
      ray.setFromCamera(pointer, camera); return ray.intersectObjects(pickables)[0]?.object
    }
    let held: { id: string; startY: number; sequence?: number; wasOpen: boolean; activated: boolean } | null = null
    let backgroundPress: {x: number; y: number} | null = null
    const down = (event: PointerEvent) => {
      if (event.button !== 0) return
      const object = hit(event); if (!object) { backgroundPress = {x:event.clientX,y:event.clientY}; return }
      if (object.userData.uf) return
      const id = object.userData.pncp as string; const archive = archives.get(id)!
      held = { id, startY: event.clientY, sequence: object.userData.sequence, wasOpen: archive.open, activated: false }
      controls.enabled = false; renderer.domElement.setPointerCapture(event.pointerId)

    }
    const move = (event: PointerEvent) => {
      if (held) {
        if (!held.activated && Math.abs(held.startY-event.clientY) < 6) return
        if (!held.activated) { held.activated = true; latest.current.onSelect(held.id); openArchive(held.id,true); setStatus('Conjunto levantado. Solte para recolher os PDFs um por um.') }
        const archive = archives.get(held.id)!
        archive.lift = Math.max(.2, Math.min(2, (held.startY - event.clientY) * .012 + .2)); request(); return
      }
      const object = hit(event); const next = object?.userData.pncp ?? ''
      if (next !== hovering) { hovering = next; renderer.domElement.style.cursor = next ? 'grab' : 'default'; request() }
    }
    const release = (event: PointerEvent) => {
      if (backgroundPress) { if (Math.hypot(event.clientX-backgroundPress.x,event.clientY-backgroundPress.y)<5) { latest.current.onOverview(); actions.current?.reset() }; backgroundPress=null }
      if (!held) return
      if (!held.activated) { if (held.wasOpen && held.sequence) latest.current.onDocument(held.id,held.sequence); held=null; controls.enabled=true; return }
      const archive = archives.get(held.id)!
      archive.lift = 0
      if (held.wasOpen && held.sequence) { latest.current.onDocument(held.id, held.sequence); openArchive(held.id, true) }
      else { openArchive(held.id, false); setExpanded(false); setStatus('PDFs retornando ao conjunto em sequência.') }
      held = null; controls.enabled = true; request()
    }
    const cancel = () => { backgroundPress = null; if (held) { openArchive(held.id, false); archives.get(held.id)!.lift = 0 }; held = null; controls.enabled = true; request() }
    const lost = (event: Event) => { event.preventDefault(); setFailed(true) }
    renderer.domElement.addEventListener('pointerdown', down, true); renderer.domElement.addEventListener('pointermove', move)
    renderer.domElement.addEventListener('pointerup', release); renderer.domElement.addEventListener('pointercancel', cancel); renderer.domElement.addEventListener('webglcontextlost', lost)
    const visibility = () => { if (document.hidden) { cancelAnimationFrame(frame); frame = 0 } else { settling = performance.now(); request() } }
    document.addEventListener('visibilitychange', visibility)
    reduce.addEventListener('change', request)
    syncBasket(latest.current.basket); setReady(true); resize()
    if (cameraPose.current) {
      camera.position.copy(cameraPose.current.position); controls.target.copy(cameraPose.current.target)
      camera.zoom = cameraPose.current.zoom * span / cameraPose.current.span
      camera.updateProjectionMatrix(); controls.update()
      tweenCamera(new THREE.Vector3(0,0,1),1,900)
    }
    return () => {
      cameraPose.current = {position:camera.position.clone(),target:controls.target.clone(),zoom:camera.zoom,span}
      disposed = true; cancelAnimationFrame(frame); observer.disconnect(); controls.dispose(); actions.current = null; invalidate.current = () => {}
      document.removeEventListener('visibilitychange', visibility)
      reduce.removeEventListener('change', request)
      renderer.domElement.removeEventListener('pointerdown', down, true); renderer.domElement.removeEventListener('pointermove', move)
      renderer.domElement.removeEventListener('pointerup', release); renderer.domElement.removeEventListener('pointercancel', cancel); renderer.domElement.removeEventListener('webglcontextlost', lost)
      resources.forEach(resource => resource.dispose()); renderer.dispose(); renderer.domElement.remove()
    }
  }, [layout])
  useEffect(() => { actions.current?.unfold(false); invalidate.current(); setExpanded(false) }, [props.selected, layout])
  useEffect(() => { actions.current?.syncBasket(props.basket) }, [props.basket, layout])
  useEffect(() => { invalidate.current() }, [props.highlighted.join('|')])
  return <div className="atlas-scene-wrap atlas-scene-rich">
    <div className="atlas-scene" ref={host} />
    <div className="atlas-state-labels" aria-label="Estados disponíveis">{stateCounts.map(({uf, count}) => <button key={uf} ref={node => { if (node) labels.current.set(uf, node); else labels.current.delete(uf) }} className="atlas-state-label" onClick={() => props.onState(uf)} aria-label={`${stateNames[uf] ?? uf}: ${count} ${count === 1 ? 'edital' : 'editais'}`}><strong>{uf}</strong><span>{count} {count === 1 ? 'edital' : 'editais'}</span></button>)}</div>
    {expanded && selectedEdital && <div className="atlas-pdf-picker" aria-label="PDFs do leque"><span className="eyebrow">{stateNames[selectedEdital.uf ?? ''] ?? selectedEdital.uf} · {selectedEdital.documents.length} PDFs</span><strong>{selectedEdital.agency}</strong><div>{selectedEdital.documents.map(file => <button key={file.sequence} aria-pressed={props.documentSequence === file.sequence} onClick={() => props.onDocument(props.selected, file.sequence)}
      onPointerDown={event => { if (event.button !== 0) return; event.currentTarget.setPointerCapture(event.pointerId); setDragFile({sequence: file.sequence, x: event.clientX, y: event.clientY}) }}
      onPointerMove={event => { if (event.currentTarget.hasPointerCapture(event.pointerId)) setDragFile({sequence: file.sequence, x: event.clientX, y: event.clientY}) }}
      onPointerUp={event => { const bounds = dropZone.current?.getBoundingClientRect(); if (bounds && event.clientX >= bounds.left && event.clientX <= bounds.right && event.clientY >= bounds.top && event.clientY <= bounds.bottom) { props.onDocument(props.selected, file.sequence); actions.current?.transport(file.sequence) }; setDragFile(null) }} onPointerCancel={() => setDragFile(null)}><span className="atlas-mini-paper">PDF</span><span>Arquivo {file.sequence}</span></button>)}</div><small>Selecione um PDF ou arraste-o até a mesa.</small></div>}
    <div ref={dropZone} className={`atlas-drop-zone ${dragFile ? 'atlas-drop-active' : ''}`}><span>MESA DE CONFERÊNCIA</span><strong>{dragFile ? 'Solte o PDF aqui' : 'Destino do PDF selecionado'}</strong><button disabled={!ready || failed || !selectedAvailable} onClick={() => actions.current?.transport(props.documentSequence)}>Levar PDF selecionado</button></div>
    {dragFile && <span aria-hidden="true" className="atlas-drag-paper" style={{left: dragFile.x, top: dragFile.y}}>PDF {dragFile.sequence}</span>}
    {failed && <p className="atlas-fallback" role="status">3D indisponível neste navegador. Use a lista de editais abaixo.</p>}
    <div className="atlas-camera"><button aria-label="Ampliar cenário" disabled={!ready || failed} onClick={() => actions.current?.zoom(1.2)}>+</button><button aria-label="Reduzir cenário" disabled={!ready || failed} onClick={() => actions.current?.zoom(1 / 1.2)}>−</button><button disabled={!ready || failed} onClick={() => actions.current?.reset()}>Vista geral</button></div>
    <div className="atlas-interactions"><span className="atlas-live-tag">ARQUIVO INTERATIVO{selectedEdital?.uf ? ` · ${stateNames[selectedEdital.uf] ?? selectedEdital.uf}` : ''}</span><button disabled={!ready || failed || !selectedAvailable} onClick={() => actions.current?.focus()}>Aproximar conjunto</button><button disabled={!ready || failed || !selectedAvailable} aria-pressed={expanded} onClick={() => actions.current?.unfold(!expanded)}>{expanded ? 'Recolher PDFs' : 'Abrir PDFs em leque'}</button><button disabled={!ready || failed || !selectedAvailable} onClick={() => actions.current?.transport(props.documentSequence)}>Levar PDF {props.documentSequence ?? props.editais.find(e => e.pncp_id === props.selected)?.documents[0]?.sequence ?? ''} à mesa</button></div>
    <p className="atlas-instructions" role="status">{status}<small>Arraste o fundo para girar · botão direito para deslocar · movimento ilustrativo, sem alteração dos documentos</small></p>
  </div>
}
