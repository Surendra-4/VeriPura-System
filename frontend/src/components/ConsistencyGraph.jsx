import React, { useEffect, useMemo, useState } from 'react';
import { getShipmentConsistencyGraph } from '../api/services';
import styles from './ConsistencyGraph.module.css';

const EDGE_COLORS = {
  MATCH: '#2dc9a5',
  MISMATCH: '#ff6f91',
};

const truncate = (text, max = 28) => {
  if (!text) return '';
  return text.length > max ? `${text.slice(0, max - 1)}…` : text;
};

const ConsistencyGraph = ({ shipmentId }) => {
  const [graph, setGraph] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeEdgeId, setActiveEdgeId] = useState(null);

  useEffect(() => {
    if (!shipmentId) return;

    let mounted = true;
    const loadGraph = async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await getShipmentConsistencyGraph(shipmentId);
        if (!mounted) return;

        setGraph(data);
        const defaultEdge = data.edges.find((edge) => edge.type === 'MISMATCH') || data.edges[0];
        setActiveEdgeId(defaultEdge?.id || null);
      } catch (err) {
        if (!mounted) return;
        setError(err.response?.data?.detail?.error || 'Consistency graph unavailable.');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    loadGraph();
    return () => {
      mounted = false;
    };
  }, [shipmentId]);

  const layout = useMemo(() => {
    if (!graph) return null;

    const documents = graph.nodes
      .filter((node) => node.node_type === 'document')
      .sort((a, b) => a.label.localeCompare(b.label));
    const entities = graph.nodes
      .filter((node) => node.node_type === 'entity')
      .sort((a, b) => {
        const aKey = `${a.metadata?.field_name || ''}:${a.label}`;
        const bKey = `${b.metadata?.field_name || ''}:${b.label}`;
        return aKey.localeCompare(bKey);
      });

    const width = 980;
    const rowGap = 88;
    const topOffset = 74;
    const maxRows = Math.max(documents.length, entities.length, 1);
    const height = topOffset * 2 + maxRows * rowGap;

    const docNodeSize = { width: 230, height: 58 };
    const entityNodeSize = { width: 250, height: 58 };
    const docX = 210;
    const entityX = 760;

    const positions = {};
    documents.forEach((node, index) => {
      positions[node.id] = { x: docX, y: topOffset + index * rowGap, kind: 'document' };
    });
    entities.forEach((node, index) => {
      positions[node.id] = { x: entityX, y: topOffset + index * rowGap, kind: 'entity' };
    });

    return {
      width,
      height,
      documents,
      entities,
      positions,
      docNodeSize,
      entityNodeSize,
    };
  }, [graph]);

  const activeEdge = useMemo(() => {
    if (!graph || !activeEdgeId) return null;
    return graph.edges.find((edge) => edge.id === activeEdgeId) || null;
  }, [graph, activeEdgeId]);

  if (loading) {
    return <div className={styles.loading}>Loading consistency graph...</div>;
  }

  if (error) {
    return <div className={styles.error}>{error}</div>;
  }

  if (!graph || !layout) {
    return null;
  }

  return (
    <div className={styles.wrapper}>
      <div className={styles.headerRow}>
        <h3>Consistency Graph</h3>
        <p>Shipment: {graph.shipment_id}</p>
      </div>

      <div className={styles.legend}>
        <span className={styles.legendItem}>
          <span className={styles.matchDot}></span> MATCH
        </span>
        <span className={styles.legendItem}>
          <span className={styles.mismatchDot}></span> MISMATCH
        </span>
      </div>

      <div className={styles.canvasWrap}>
        <svg
          className={styles.canvas}
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          preserveAspectRatio="xMidYMid meet"
        >
          <text x={80} y={38} className={styles.columnTitle}>
            Documents
          </text>
          <text x={640} y={38} className={styles.columnTitle}>
            Extracted Entities
          </text>

          {graph.edges.map((edge) => {
            const source = layout.positions[edge.source];
            const target = layout.positions[edge.target];
            if (!source || !target) return null;

            const startX = source.x + layout.docNodeSize.width / 2;
            const endX = target.x - layout.entityNodeSize.width / 2;
            const startY = source.y;
            const endY = target.y;
            const cp1X = startX + 110;
            const cp2X = endX - 110;
            const d = `M ${startX} ${startY} C ${cp1X} ${startY}, ${cp2X} ${endY}, ${endX} ${endY}`;
            const isActive = activeEdgeId === edge.id;

            return (
              <path
                key={edge.id}
                d={d}
                className={styles.edgePath}
                stroke={EDGE_COLORS[edge.type] || '#6ba8c9'}
                strokeWidth={isActive ? 4 : 2.2}
                opacity={isActive ? 1 : 0.72}
                onClick={() => setActiveEdgeId(edge.id)}
              />
            );
          })}

          {layout.documents.map((node) => {
            const pos = layout.positions[node.id];
            return (
              <g key={node.id} transform={`translate(${pos.x - layout.docNodeSize.width / 2}, ${pos.y - 29})`}>
                <rect
                  className={styles.docNode}
                  width={layout.docNodeSize.width}
                  height={layout.docNodeSize.height}
                  rx="12"
                />
                <text x="12" y="24" className={styles.nodeTitle}>
                  {truncate(node.label, 30)}
                </text>
                <text x="12" y="42" className={styles.nodeMeta}>
                  {truncate(node.metadata?.record_batch_id || '', 32)}
                </text>
              </g>
            );
          })}

          {layout.entities.map((node) => {
            const pos = layout.positions[node.id];
            const fieldName = node.metadata?.field_name || 'field';
            return (
              <g
                key={node.id}
                transform={`translate(${pos.x - layout.entityNodeSize.width / 2}, ${pos.y - 29})`}
              >
                <rect
                  className={styles.entityNode}
                  width={layout.entityNodeSize.width}
                  height={layout.entityNodeSize.height}
                  rx="12"
                />
                <text x="12" y="22" className={styles.entityField}>
                  {fieldName}
                </text>
                <text x="12" y="42" className={styles.nodeMeta}>
                  {truncate(node.label, 34)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {activeEdge && (
        <div className={styles.edgeDetails}>
          <p>
            <strong>{activeEdge.type}</strong> on <strong>{activeEdge.field_name}</strong>
          </p>
          <p>{activeEdge.explanation}</p>
        </div>
      )}
    </div>
  );
};

export default ConsistencyGraph;
