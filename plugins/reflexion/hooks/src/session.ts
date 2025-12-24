import {mkdir, readFile, writeFile} from 'node:fs/promises'
import {tmpdir} from 'node:os'
import * as path from 'node:path'
import type {HookPayload} from './lib'

const SESSIONS_DIR = path.join(tmpdir(), 'claude-hooks-sessions')

/**
 * Session data entry representing a single hook invocation.
 * Only specific hook types (Stop, SubagentStop, Notification, UserPromptSubmit)
 * are configured in settings.json, so only these types will be saved.
 * This reduces memory usage and focuses on relevant debugging information.
 */
export interface SessionData {
  timestamp: string
  hookType: string
  payload: HookPayload
}

/**
 * Saves session data for hook invocations.
 * Only hooks configured in settings.json will be invoked and saved.
 *
 * @param hookType - The type of hook being invoked
 * @param payload - The hook payload data
 * @returns Array of all session data entries for this session
 */
export async function saveSessionData(hookType: string, payload: HookPayload): Promise<Array<SessionData>> {
  try {
    // Ensure sessions directory exists
    await mkdir(SESSIONS_DIR, {recursive: true})

    const timestamp = new Date().toISOString()
    const sessionFile = path.join(SESSIONS_DIR, `${payload.session_id}.json`)

    let sessionData: Array<SessionData> = []
    try {
      const existing = await readFile(sessionFile, 'utf-8')
      sessionData = JSON.parse(existing)
    } catch {
      // File doesn't exist yet
    }

    sessionData.push({
      timestamp,
      hookType,
      payload,
    })

    await writeFile(sessionFile, JSON.stringify(sessionData, null, 2))

    return sessionData
  } catch (error) {
    console.error('Failed to save session data:', error)
    return []
  }
}
