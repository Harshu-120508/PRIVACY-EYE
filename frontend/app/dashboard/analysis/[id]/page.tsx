import AnalysisDetailClient from './AnalysisDetailClient'

export function generateStaticParams() {
  return [{ id: 'placeholder' }]
}

export default function AnalysisDetailPage({ params }: { params: { id: string } }) {
  return <AnalysisDetailClient id={params?.id} />
}
