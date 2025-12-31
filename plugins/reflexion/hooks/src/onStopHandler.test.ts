import { describe, it, expect, beforeEach } from 'vitest'
import type { StopPayload } from './lib'
import type { SessionData } from './session'

import { stop, isContainsWord } from './onStopHandler'

const createMockPayload = (cwd: string = '/test/cwd'): StopPayload => ({
  cwd,
  session_id: 'test-session-123',
  transcript_path: '/tmp/transcript.jsonl',
  hook_event_name: 'Stop',
  stop_hook_active: true,
})

const createUserPromptSession = (prompt: string, timestamp: string = new Date().toISOString()): SessionData => ({
  timestamp,
  hookType: 'UserPromptSubmit',
  payload: {
    session_id: 'test-session-123',
    transcript_path: '/tmp/transcript.jsonl',
    hook_event_name: 'UserPromptSubmit',
    prompt,
  } as any,
})

const createStopSession = (timestamp: string = new Date().toISOString()): SessionData => ({
  timestamp,
  hookType: 'Stop',
  payload: {
    session_id: 'test-session-123',
    transcript_path: '/tmp/transcript.jsonl',
    hook_event_name: 'Stop',
    stop_hook_active: true,
  } as any,
})

describe('isContainsWord', () => {
  describe('positive cases - should match standalone word', () => {
    it('should match word at the start of sentence', () => {
      expect(isContainsWord('reflect on this code', 'reflect')).toBe(true)
    })

    it('should match word at the end of sentence', () => {
      expect(isContainsWord('please reflect', 'reflect')).toBe(true)
    })

    it('should match word in the middle of sentence', () => {
      expect(isContainsWord('please reflect on this', 'reflect')).toBe(true)
    })

    it('should match when prompt is only the word', () => {
      expect(isContainsWord('reflect', 'reflect')).toBe(true)
    })

    it('should match case-insensitively', () => {
      expect(isContainsWord('REFLECT on this', 'reflect')).toBe(true)
      expect(isContainsWord('Reflect on this', 'reflect')).toBe(true)
      expect(isContainsWord('ReFLeCt on this', 'reflect')).toBe(true)
    })

    it('should match with leading/trailing whitespace in prompt', () => {
      expect(isContainsWord('  reflect on this  ', 'reflect')).toBe(true)
    })

    it('should match word followed by punctuation', () => {
      expect(isContainsWord('please reflect.', 'reflect')).toBe(true)
      expect(isContainsWord('please reflect!', 'reflect')).toBe(true)
      expect(isContainsWord('please reflect?', 'reflect')).toBe(true)
      expect(isContainsWord('please reflect,', 'reflect')).toBe(true)
    })

    it('should match word preceded by punctuation', () => {
      expect(isContainsWord('done. reflect on this', 'reflect')).toBe(true)
    })

    it('should match "self-reflect" (hyphen is a word boundary)', () => {
      // Hyphen acts as word boundary in regex, so "reflect" in "self-reflect" is a standalone word
      expect(isContainsWord('please self-reflect', 'reflect')).toBe(true)
    })
  })

  describe('negative cases - should NOT match word as part of another word', () => {
    it('should NOT match "reflection"', () => {
      expect(isContainsWord('write a reflection on this', 'reflect')).toBe(false)
    })

    it('should NOT match "reflective"', () => {
      expect(isContainsWord('be reflective about this', 'reflect')).toBe(false)
    })

    it('should NOT match "reflector"', () => {
      expect(isContainsWord('use a reflector', 'reflect')).toBe(false)
    })

    it('should NOT match "reflected"', () => {
      expect(isContainsWord('I reflected on this', 'reflect')).toBe(false)
    })

    it('should NOT match "reflecting"', () => {
      expect(isContainsWord('I am reflecting on this', 'reflect')).toBe(false)
    })

    it('should NOT match when word is absent', () => {
      expect(isContainsWord('do something else', 'reflect')).toBe(false)
    })

    it('should NOT match empty prompt', () => {
      expect(isContainsWord('', 'reflect')).toBe(false)
    })
  })

  describe('slash command exclusion - should NOT match when preceded by / or :', () => {
    it('should NOT match "/reflect" (direct slash command)', () => {
      expect(isContainsWord('/reflect', 'reflect')).toBe(false)
    })

    it('should NOT match "/reflexion:reflect" (namespaced slash command)', () => {
      expect(isContainsWord('/reflexion:reflect', 'reflect')).toBe(false)
    })

    it('should NOT match ":reflect" (colon prefix)', () => {
      expect(isContainsWord(':reflect', 'reflect')).toBe(false)
    })

    it('should NOT match "/reflect on this" (slash command in sentence)', () => {
      expect(isContainsWord('/reflect on this', 'reflect')).toBe(false)
    })

    it('should NOT match "run /reflect" (slash command after other text)', () => {
      expect(isContainsWord('run /reflect', 'reflect')).toBe(false)
    })

    it('should NOT match "run /reflexion:reflect and continue"', () => {
      expect(isContainsWord('run /reflexion:reflect and continue', 'reflect')).toBe(false)
    })

    it('should NOT match "execute :reflect now"', () => {
      expect(isContainsWord('execute :reflect now', 'reflect')).toBe(false)
    })

    it('should still match "reflect" when slash command AND normal word both present', () => {
      // If user says "run /reflexion:reflect and then reflect on it", we SHOULD trigger
      // because there's a standalone "reflect" at the end
      expect(isContainsWord('run /reflexion:reflect and then reflect on it', 'reflect')).toBe(true)
    })
  })
})

describe('onStopHandler', () => {
  describe('session validation', () => {
    it('should skip reflection when session has no data', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = []

      const result = await stop(payload, sessionData)

      expect(result).toEqual({ debug: '⚠️ Not enough session data found, skipping reflection' })
    })

    it('should skip reflection when session has only non-relevant hooks', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        {
          timestamp: new Date().toISOString(),
          hookType: 'SessionStart',
          payload: {} as any,
        },
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({ debug: '⚠️ Not enough session data found, skipping reflection' })
    })
  })

  describe('consecutive STOP detection (cycle prevention)', () => {
    it('should detect and prevent consecutive STOP invocations', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('reflect on this'),
        createStopSession(),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({ debug: '⚠️ Detected consecutive STOP invocations, preventing cycle' })
    })

    it('should allow non-consecutive STOP invocations', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('reflect on this'),
        createStopSession(),
        createUserPromptSession('reflect again'),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({
        decision: 'block',
        reason: 'You MUST use SlashCommand tool to execute the command /reflexion:reflect',
      })
    })
  })

  describe('trigger word detection', () => {
    it('should block and request reflection when "reflect" word is in prompt', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('please reflect on this code'),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({
        decision: 'block',
        reason: 'You MUST use SlashCommand tool to execute the command /reflexion:reflect',
      })
    })

    it('should skip reflection when "reflect" word is NOT in prompt', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('fix the bug in this code'),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({ debug: '⚠️ Reflect word not found in the user prompt, skipping reflection' })
    })

    it('should skip reflection when prompt contains "reflection" (not standalone "reflect")', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('write a reflection on this code'),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({ debug: '⚠️ Reflect word not found in the user prompt, skipping reflection' })
    })

    it('should skip reflection when prompt contains "reflective" (not standalone "reflect")', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('be reflective about this'),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({ debug: '⚠️ Reflect word not found in the user prompt, skipping reflection' })
    })

    it('should trigger reflection when prompt has "reflect" with punctuation', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('after fixing, reflect.'),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({
        decision: 'block',
        reason: 'You MUST use SlashCommand tool to execute the command /reflexion:reflect',
      })
    })

    it('should trigger reflection case-insensitively', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('REFLECT on this'),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({
        decision: 'block',
        reason: 'You MUST use SlashCommand tool to execute the command /reflexion:reflect',
      })
    })
  })

  describe('uses last user prompt', () => {
    it('should check the last user prompt, not earlier ones', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('reflect on this'),
        createStopSession(),
        createUserPromptSession('fix the bug'),  // last prompt without "reflect"
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({ debug: '⚠️ Reflect word not found in the user prompt, skipping reflection' })
    })

    it('should trigger when last prompt has "reflect" even if earlier prompts did not', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('fix the bug'),
        createStopSession(),
        createUserPromptSession('now reflect on the changes'),  // last prompt with "reflect"
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({
        decision: 'block',
        reason: 'You MUST use SlashCommand tool to execute the command /reflexion:reflect',
      })
    })
  })

  describe('slash command exclusion in prompts', () => {
    it('should NOT trigger when prompt is a slash command "/reflexion:reflect"', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('/reflexion:reflect'),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({ debug: '⚠️ Reflect word not found in the user prompt, skipping reflection' })
    })

    it('should NOT trigger when prompt contains slash command "run /reflexion:reflect"', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('run /reflexion:reflect'),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({ debug: '⚠️ Reflect word not found in the user prompt, skipping reflection' })
    })

    it('should trigger when prompt has both slash command and standalone reflect', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('run /reflexion:reflect and then reflect on it'),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({
        decision: 'block',
        reason: 'You MUST use SlashCommand tool to execute the command /reflexion:reflect',
      })
    })
  })

  describe('edge cases', () => {
    it('should trigger reflection with minimal valid session (UserPromptSubmit + Stop)', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        createUserPromptSession('reflect'),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({
        decision: 'block',
        reason: 'You MUST use SlashCommand tool to execute the command /reflexion:reflect',
      })
    })

    it('should handle complex realistic session', async () => {
      const payload = createMockPayload()
      const sessionData: SessionData[] = [
        {
          timestamp: new Date().toISOString(),
          hookType: 'SessionStart',
          payload: {} as any,
        },
        createUserPromptSession('implement the feature'),
        {
          timestamp: new Date().toISOString(),
          hookType: 'PreToolUse',
          payload: {} as any,
        },
        {
          timestamp: new Date().toISOString(),
          hookType: 'PostToolUse',
          payload: {} as any,
        },
        createUserPromptSession('now reflect on the implementation'),
        createStopSession(),
      ]

      const result = await stop(payload, sessionData)

      expect(result).toEqual({
        decision: 'block',
        reason: 'You MUST use SlashCommand tool to execute the command /reflexion:reflect',
      })
    })
  })
})
