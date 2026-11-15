// The pipeline diagram, used by the README and the report.
// From the project root:  typst compile --root . experiments/pipeline.typ figures/pipeline.svg
// The first compile downloads the fletcher package from the Typst registry.

#import "@preview/fletcher:0.5.8": diagram, node, edge

#set page(width: auto, height: auto, margin: 6pt)
#set text(size: 9pt)
#let tool(name) = text(size: 8pt, fill: luma(90), raw(name))
#diagram(
  spacing: (15mm, 9mm),
  node-shape: rect,
  node-stroke: 0.6pt + luma(110),
  node-fill: luma(245),
  node-corner-radius: 2pt,
  node-inset: 5pt,
  edge-stroke: 0.7pt,
  node((0, 1), [intersection\ #text(size: 7.5pt)[JSON]], name: <in>),
  node((1, 1), [timing\ #text(size: 7.5pt)[in steps]], name: <tim>),
  node((2, 0), [LTL spec], name: <ltl>),
  node((2, 2), [GR(1) spec\ #text(size: 7.5pt)[with counters]], name: <gr1>),
  node((4, 2), [strategy\ #text(size: 7.5pt)[BDD]], name: <bdd>),
  node((5, 1), [circuit\ #text(size: 7.5pt)[AIGER]], name: <aig>, stroke: 0.9pt + rgb("#a51c30")),
  node((6, 0), [model checker\ #text(size: 7.5pt)[NuSMV]], name: <smv>, stroke: 0.9pt + rgb("#a51c30")),
  node((6, 2), [timeline], name: <sim>),
  edge(<in>, <tim>, "-|>", tool("timing.py"), label-side: left),
  edge(<tim>, (1, 0), <ltl>, "-|>", tool("genspec.py"), label-pos: 0.3, label-side: left),
  edge(<tim>, (1, 2), <gr1>, "-|>", tool("gr1spec.py"), label-pos: 0.3, label-side: right),
  edge(<ltl>, (5, 0), <aig>, "-|>", tool("synth.py (ltlsynt)"), label-pos: 0.3, label-side: left),
  edge(<gr1>, <bdd>, "-|>", tool("gr1synth.py (Slugs)"), label-side: left),
  edge(<bdd>, (5, 2), <aig>, "-|>", tool("bdd2aag.py"), label-pos: 0.75, label-side: right),
  edge(<aig>, (6, 1), <smv>, "-|>", tool("aag2smv.py"), label-pos: 0.3, label-side: left),
  edge(<aig>, (6, 1), <sim>, "-|>", tool("simulate.py"), label-pos: 0.75, label-side: left),
  edge(<ltl>, (2, -0.8), (6, -0.8), <smv>, "--|>", tool("verify.py (NuSMV): every LTL property"),
    label-pos: 0.5, label-side: left),
)
