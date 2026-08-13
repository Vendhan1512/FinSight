import React, { useState } from 'react';
import { Info } from 'lucide-react';
import type { LineageMetadata } from '../../api/intelligence';

interface LineageTooltipProps {
  lineage: LineageMetadata;
}

export const LineageTooltip: React.FC<LineageTooltipProps> = ({ lineage }) => {
  const [show, setShow] = useState(false);

  return (
    <div className="relative inline-block ml-2" onMouseEnter={() => setShow(true)} onMouseLeave={() => setShow(false)}>
      <Info size={16} className="text-textMuted cursor-pointer hover:text-primary transition-colors" />
      {show && (
        <div className="absolute z-10 w-64 p-3 mt-2 -ml-32 text-xs text-textMain bg-surfaceHighlight border border-white/10 rounded shadow-lg backdrop-blur-xl">
          <p className="font-semibold mb-1 border-b border-white/10 pb-1">Data Provenance</p>
          <div className="grid grid-cols-2 gap-x-2 gap-y-1">
            <span className="text-textMuted">Provenance ID:</span>
            <span className="truncate" title={lineage.provenance_id}>{lineage.provenance_id.split('-')[0]}...</span>
            
            {lineage.model_version && (
              <>
                <span className="text-textMuted">Model Ver:</span>
                <span>{lineage.model_version}</span>
              </>
            )}
            
            {lineage.methodology_version && (
              <>
                <span className="text-textMuted">Methodology:</span>
                <span>{lineage.methodology_version}</span>
              </>
            )}
            
            <span className="text-textMuted">Data Cutoff:</span>
            <span>{new Date(lineage.data_cutoff).toLocaleString()}</span>
          </div>
        </div>
      )}
    </div>
  );
};
