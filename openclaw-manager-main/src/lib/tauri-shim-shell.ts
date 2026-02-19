export async function open(target: string): Promise<void> {
  if (typeof window === 'undefined') {
    return;
  }

  window.open(target, '_blank', 'noopener,noreferrer');
}
