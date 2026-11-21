import { useEffect, useId, useRef, useState } from 'react'
import type { Html5Qrcode } from 'html5-qrcode'

interface QrScannerProps {
  onScan: (value: string) => void
}

export function QrScanner({ onScan }: QrScannerProps) {
  const elementId = `qr-reader-${useId().replaceAll(':', '')}`
  const scannerRef = useRef<Html5Qrcode | null>(null)
  const onScanRef = useRef(onScan)
  const [scanning, setScanning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    onScanRef.current = onScan
  }, [onScan])

  useEffect(() => {
    return () => {
      const scanner = scannerRef.current
      if (scanner?.isScanning) {
        void scanner.stop()
          .then(() => scanner.clear())
          .catch((stopError: unknown) => {
            console.error('QR tarayıcı kapatılamadı.', stopError)
          })
      }
    }
  }, [])

  async function startScanner() {
    setError(null)
    try {
      const { Html5Qrcode: QrScanner } = await import('html5-qrcode')
      const activeScanner = new QrScanner(elementId)
      scannerRef.current = activeScanner
      await activeScanner.start(
        { facingMode: 'environment' },
        { fps: 10, qrbox: { width: 220, height: 220 } },
        (decodedText) => {
          onScanRef.current(decodedText)
          if (activeScanner.isScanning) {
            void activeScanner.stop()
              .then(() => activeScanner.clear())
              .then(() => {
                scannerRef.current = null
                setScanning(false)
              })
              .catch((stopError: unknown) => {
                setError(
                  stopError instanceof Error
                    ? stopError.message
                    : 'QR tarayıcı kapatılamadı.',
                )
              })
          }
        },
        () => undefined,
      )
      setScanning(true)
    } catch (startError) {
      const scanner = scannerRef.current
      scannerRef.current = null
      if (scanner?.isScanning) {
        try {
          await scanner.stop()
          scanner.clear()
        } catch (cleanupError) {
          console.error('Başlatma sonrası QR tarayıcı temizlenemedi.', cleanupError)
        }
      }
      setError(
        startError instanceof Error
          ? startError.message
          : 'Kamera başlatılamadı; QR verisini elle yapıştırabilirsiniz.',
      )
    }
  }

  async function stopScanner() {
    const scanner = scannerRef.current
    if (!scanner?.isScanning) return
    try {
      await scanner.stop()
      scanner.clear()
      scannerRef.current = null
      setScanning(false)
    } catch (stopError) {
      setError(
        stopError instanceof Error
          ? stopError.message
          : 'QR tarayıcı kapatılamadı.',
      )
    }
  }

  return (
    <div className="qr-scanner">
      <div id={elementId} />
      {scanning ? (
        <button className="button button-secondary" onClick={stopScanner} type="button">
          Kamerayı durdur
        </button>
      ) : (
        <button className="button button-secondary" onClick={startScanner} type="button">
          Kamerayla QR tara
        </button>
      )}
      {error && <p className="notice notice-error">{error}</p>}
    </div>
  )
}
