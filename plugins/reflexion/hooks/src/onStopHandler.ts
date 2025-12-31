import { UserPromptSubmitPayload, type StopHandler } from "./lib"

const TRIGGER_WORD = "reflect"
const DEFAULT_REFLECT_PROMPT = "You MUST use SlashCommand tool to execute the command /reflexion:reflect"

/**
 * Stop handler - called when Claude stops
 * if "reflect" word was present in the user prompt, 
 * will block the stop and ask LLM to execute the command /reflexion:reflect
 */
export const stop: StopHandler = async (payload, sessionData) => {
    // Filter to only relevant hooks for reflection logic
    const invocations = sessionData
      // All other hooks are irrelevant to prevent cycles
      .filter(entry => entry.hookType === 'UserPromptSubmit' || entry.hookType === 'Stop')

    if (invocations.length < 2) {
      return {debug: '⚠️ Not enough session data found, skipping reflection'}
    }

    // Last hook before current stop triggered
    const lastHook = invocations[invocations.length - 2]

    // Validate no consecutive STOP calls (cycle detection)
    // last hook allways will be Stop, so we need to check the second to last only
    if (lastHook.hookType !== 'UserPromptSubmit'){
      return {debug: '⚠️ Detected consecutive STOP invocations, preventing cycle'}
    }

    const {prompt: lastUserPrompt} = lastHook.payload as UserPromptSubmitPayload

    if (!isContainsWord(lastUserPrompt, TRIGGER_WORD)){
      return {debug: '⚠️ Reflect word not found in the user prompt, skipping reflection'}
    }

    return { decision: "block", reason: DEFAULT_REFLECT_PROMPT, debug: invocations }
}

/**
 * Check if prompt contains word as a standalone word (not part of another word).
 * Uses word boundary regex to avoid matching "reflective" or "reflection" when looking for "reflect".
 * Uses negative lookbehind to exclude slash commands (e.g., /reflect, :reflect, /reflexion:reflect).
 */
export const isContainsWord = (prompt: string, word: string) => {
    const sanitized = prompt.toLowerCase().trim()
    // Negative lookbehind (?<![:/]) ensures the word is not preceded by / or :
    // This prevents triggering on slash commands like /reflect or /reflexion:reflect
    const wordBoundaryRegex = new RegExp(`(?<![:/])\\b${word}\\b`)
    return wordBoundaryRegex.test(sanitized)
}