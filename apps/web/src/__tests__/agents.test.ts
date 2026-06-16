import { describe, it, expect } from 'vitest'
import { AGENT_DEFS, findAgentDef } from '../data/agents'

// Architecture regression guard for the agent catalog shown in the dashboard.
// The old panels hard-coded fake paths (agents/steps/*.py) that did not exist;
// these tests ensure the catalog stays truthful and lookups keep working.

describe('agent catalog', () => {
  const STALE = [
    'agents/steps',
    'scripts/run_demo_pipeline.py',
    'run_demo_pipeline.py',
    'agents/server.py',
  ]

  it('contains no stale / non-existent code paths', () => {
    for (const def of AGENT_DEFS) {
      const blob = [def.codeLocation, ...def.inputs, ...def.outputs, def.changeHint].join(' ')
      for (const bad of STALE) {
        expect(blob, `agent ${def.id} references stale path "${bad}"`).not.toContain(bad)
      }
    }
  })

  it('uses the new core/generator/src/templates path, not the old generator/src/templates', () => {
    const codegen = findAgentDef('code_generation')
    expect(codegen).not.toBeNull()
    const inputs = codegen!.inputs.join(' ')
    expect(inputs).toContain('core/generator/src/templates')
    // The bare (old) form must not appear without the core/ prefix.
    expect(inputs).not.toMatch(/(^|[^/])generator\/src\/templates/)
  })

  it('uses the new data/inputs paths, not legacy data/samples or data/real_inputs', () => {
    const market = findAgentDef('market_input')
    expect(market).not.toBeNull()
    const inputs = market!.inputs.join(' ')
    expect(inputs).toContain('data/inputs/demo/apps.json')
    expect(inputs).toContain('data/inputs/real/apps.json')
    expect(inputs).not.toContain('data/samples')
    expect(inputs).not.toContain('data/real_inputs')
  })

  it('every code location points at core/pipeline/runner.py', () => {
    for (const def of AGENT_DEFS) {
      expect(def.codeLocation, `agent ${def.id}`).toContain('core/pipeline/runner.py')
    }
  })

  it('looks up by both step id and agent name', () => {
    expect(findAgentDef('market_input')?.id).toBe('market_input')
    expect(findAgentDef('MarketInputAgent')?.id).toBe('market_input')
    expect(findAgentDef('readiness')?.id).toBe('readiness')
    expect(findAgentDef('nonexistent')).toBeNull()
    expect(findAgentDef(undefined)).toBeNull()
  })
})
