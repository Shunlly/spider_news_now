/**
 * 导出对话框组件
 * ExportDialog Component
 * T155: Create ExportDialog component
 *
 * 提供数据导出功能，支持多种格式选择。
 */

import { useState } from 'react';
import { Download, FileText, FileSpreadsheet, FileJson, Loader2 } from 'lucide-react';
import { StoneModal, StoneButton } from '@/components/ui';
import clsx from 'clsx';

export type ExportFormat = 'csv' | 'json' | 'excel';

export interface ExportOptions {
  format: ExportFormat;
  includeHeaders?: boolean;
  dateRange?: {
    start: string;
    end: string;
  };
  fields?: string[];
}

export interface ExportDialogProps {
  open: boolean;
  onClose: () => void;
  onExport: (options: ExportOptions) => Promise<void>;
  title?: string;
  dataType?: string;
  availableFields?: { key: string; label: string }[];
  defaultFormat?: ExportFormat;
}

const formatConfig = {
  csv: {
    icon: FileText,
    label: 'CSV',
    description: '逗号分隔值，适用于 Excel 和数据分析工具',
    extension: '.csv',
  },
  json: {
    icon: FileJson,
    label: 'JSON',
    description: '结构化数据格式，适用于程序处理',
    extension: '.json',
  },
  excel: {
    icon: FileSpreadsheet,
    label: 'Excel',
    description: 'Microsoft Excel 格式，支持多工作表',
    extension: '.xlsx',
  },
};

export function ExportDialog({
  open,
  onClose,
  onExport,
  title = '导出数据',
  dataType = '数据',
  availableFields,
  defaultFormat = 'csv',
}: ExportDialogProps) {
  const [format, setFormat] = useState<ExportFormat>(defaultFormat);
  const [includeHeaders, setIncludeHeaders] = useState(true);
  const [selectedFields, setSelectedFields] = useState<Set<string>>(
    new Set(availableFields?.map((f) => f.key) || [])
  );
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleExport = async () => {
    setExporting(true);
    setError(null);

    try {
      await onExport({
        format,
        includeHeaders,
        fields: availableFields ? Array.from(selectedFields) : undefined,
      });
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : '导出失败');
    } finally {
      setExporting(false);
    }
  };

  const toggleField = (key: string) => {
    const newSelected = new Set(selectedFields);
    if (newSelected.has(key)) {
      newSelected.delete(key);
    } else {
      newSelected.add(key);
    }
    setSelectedFields(newSelected);
  };

  const toggleAllFields = () => {
    if (selectedFields.size === availableFields?.length) {
      setSelectedFields(new Set());
    } else {
      setSelectedFields(new Set(availableFields?.map((f) => f.key) || []));
    }
  };

  return (
    <StoneModal open={open} onClose={onClose} title={title}>
      <div className="space-y-6">
        {/* 格式选择 */}
        <div>
          <label className="block text-sm text-slate-400 mb-3">导出格式</label>
          <div className="grid grid-cols-3 gap-3">
            {(Object.entries(formatConfig) as [ExportFormat, typeof formatConfig.csv][]).map(
              ([key, config]) => {
                const Icon = config.icon;
                const isSelected = format === key;

                return (
                  <button
                    key={key}
                    onClick={() => setFormat(key)}
                    className={clsx(
                      'flex flex-col items-center p-4 rounded-lg border transition-all',
                      isSelected
                        ? 'border-cyan-500 bg-cyan-500/10'
                        : 'border-slate-700 hover:border-slate-600 bg-slate-800/50'
                    )}
                  >
                    <Icon
                      className={clsx(
                        'w-8 h-8 mb-2',
                        isSelected ? 'text-cyan-400' : 'text-slate-400'
                      )}
                    />
                    <span
                      className={clsx(
                        'font-medium',
                        isSelected ? 'text-cyan-400' : 'text-slate-300'
                      )}
                    >
                      {config.label}
                    </span>
                    <span className="text-xs text-slate-500 mt-1">{config.extension}</span>
                  </button>
                );
              }
            )}
          </div>
          <p className="text-sm text-slate-500 mt-2">{formatConfig[format].description}</p>
        </div>

        {/* 选项 */}
        {format !== 'json' && (
          <div>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={includeHeaders}
                onChange={(e) => setIncludeHeaders(e.target.checked)}
                className="rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
              />
              <span className="text-slate-300">包含表头</span>
            </label>
          </div>
        )}

        {/* 字段选择 */}
        {availableFields && availableFields.length > 0 && (
          <div>
            <div className="flex items-center justify-between mb-3">
              <label className="text-sm text-slate-400">选择导出字段</label>
              <button
                onClick={toggleAllFields}
                className="text-sm text-cyan-400 hover:text-cyan-300"
              >
                {selectedFields.size === availableFields.length ? '取消全选' : '全选'}
              </button>
            </div>
            <div className="grid grid-cols-2 gap-2 max-h-40 overflow-y-auto">
              {availableFields.map((field) => (
                <label
                  key={field.key}
                  className="flex items-center gap-2 p-2 rounded-lg hover:bg-slate-800/50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedFields.has(field.key)}
                    onChange={() => toggleField(field.key)}
                    className="rounded border-slate-600 bg-slate-800 text-cyan-500 focus:ring-cyan-500"
                  />
                  <span className="text-sm text-slate-300">{field.label}</span>
                </label>
              ))}
            </div>
          </div>
        )}

        {/* 错误提示 */}
        {error && (
          <div className="p-3 bg-red-500/10 border border-red-500/30 rounded-lg">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        )}

        {/* 操作按钮 */}
        <div className="flex justify-end gap-3 pt-4 border-t border-slate-700/50">
          <StoneButton onClick={onClose} disabled={exporting}>
            取消
          </StoneButton>
          <StoneButton
            variant="primary"
            onClick={handleExport}
            disabled={exporting || (availableFields && selectedFields.size === 0)}
          >
            {exporting ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                导出中...
              </>
            ) : (
              <>
                <Download className="w-4 h-4 mr-2" />
                导出 {dataType}
              </>
            )}
          </StoneButton>
        </div>
      </div>
    </StoneModal>
  );
}

export default ExportDialog;
