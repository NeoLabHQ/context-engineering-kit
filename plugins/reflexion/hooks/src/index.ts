#!/usr/bin/env bun

import type {
  NotificationHandler,
  PostToolUseHandler,
  PreCompactHandler,
  PreToolUseHandler,
  SessionStartHandler,
  SubagentStopHandler,
  UserPromptSubmitHandler,
} from './lib'
import {runHook, log} from './lib'
import { stop } from './onStopHandler'

// SessionStart handler - called when a new Claude session starts
const sessionStart: SessionStartHandler = async (payload) => {

  // Example: Log session start with source
  log(`🚀 New session started from: ${payload.source}`)
  log(`📍 Session ID: ${payload.session_id}`)

  // Example: Load user preferences or configuration
  // const userConfig = await loadUserPreferences()

  // Example: Set up session-specific resources
  // await initializeSessionResources(payload.session_id)

  // Example: Apply different behavior based on session source
  if (payload.source === 'vscode') {
    log('👨‍💻 VS Code session detected - enabling IDE-specific features')
  } else if (payload.source === 'web') {
    log('🌐 Web session detected')
  }

  // Add your custom session initialization logic here

  return {} // Empty object means continue normally
}

// PreToolUse handler - called before Claude uses any tool
// This handler can block tool execution by returning a deny decision
const preToolUse: PreToolUseHandler = async (payload) => {

  // Example: Log when Claude is about to edit files
  if (payload.tool_name === 'Edit' && payload.tool_input) {
    const {file_path} = payload.tool_input as {file_path: string}
    log(`📝 Claude is editing: ${file_path}`)
  }

  // Example: Track bash commands
  if (payload.tool_name === 'Bash' && payload.tool_input && 'command' in payload.tool_input) {
    const command = (payload.tool_input as {command: string}).command
    log(`🚀 Running command: ${command}`)

    // Block dangerous commands
    if (command.includes('rm -rf /') || command.includes('rm -rf ~')) {
      console.error('❌ Dangerous command detected! Blocking execution.')
      return {
        permissionDecision: 'deny',
        permissionDecisionReason: `Dangerous command detected: ${command}`,
      }
    }
  }

  // Add your custom logic here!
  // You have full TypeScript support and can use any npm packages

  return {} // Empty object means continue with default behavior
}

// PostToolUse handler - called after Claude uses a tool
const postToolUse: PostToolUseHandler = async (payload) => {

  // Example: React to successful file writes
  if (payload.tool_name === 'Write' && payload.tool_response) {
    log(`✅ File written successfully!`)
  }

  // Add your custom post-processing logic here

  return {} // Return empty object to continue normally
}

// Notification handler - receive Claude's notifications
const notification: NotificationHandler = async (payload) => {

  // Example: Log Claude's progress
  log(`🔔 ${payload.message}`)

  return {} // Return empty object to continue normally
}



// SubagentStop handler - called when a Claude subagent (Task tool) stops
const subagentStop: SubagentStopHandler = async (payload) => {

  // Example: Log subagent completion
  log(`🤖 Subagent task completed`)

  // Add your custom subagent cleanup logic here
  // Note: Be careful with stop_hook_active to avoid infinite loops
  if (payload.stop_hook_active) {
    log('⚠️  Stop hook is already active, skipping additional processing')
  }

  return {} // Return empty object to continue normally
}

// UserPromptSubmit handler - called when the user submits a prompt
const userPromptSubmit: UserPromptSubmitHandler = async (payload) => {

  // Example: Log user prompts
  log(`💬 User prompt: ${payload.prompt}`)

  // By default continue normally and just record user prompt
  return {}
}

// PreCompact handler - called before Claude compacts the conversation
const preCompact: PreCompactHandler = async (payload) => {

  // Example: Log compact events
  log(`🗜️  Compact triggered: ${payload.trigger}`)

  // Example: Block automatic compaction during critical operations
  if (payload.trigger === 'auto') {
    // You could check if critical operations are in progress
    // For now, we'll allow all compactions
    log('📋 Allowing automatic compaction')
  }

  // Add your custom compaction logic here

  return {} // Empty object means allow compaction
}

const main = (): void => {
  // Run the hook with our handlers
  runHook({
    SessionStart: sessionStart,
    PreToolUse: preToolUse,
    PostToolUse: postToolUse,
    Notification: notification,
    Stop: stop,
    SubagentStop: subagentStop,
    UserPromptSubmit: userPromptSubmit,
    PreCompact: preCompact,
  }).catch(error => {
    console.error('Hook error:', error)
    process.exit(1)
  })
}

main()