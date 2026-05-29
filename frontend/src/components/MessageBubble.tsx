interface Props {
  text: string
  isStreaming: boolean
}

export default function MessageBubble({ text, isStreaming }: Props) {
  if (!text) return null
  return (
    <p className={`text-sm leading-relaxed text-white/90 whitespace-pre-wrap ${isStreaming ? 'typing-cursor' : ''}`}>
      {text}
    </p>
  )
}
