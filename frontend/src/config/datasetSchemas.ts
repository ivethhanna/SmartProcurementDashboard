export type FieldType = "text" | "number" | "select" | "boolean";

export interface FieldOption {
  value: string;
  label: string;
}

export interface ColumnConfig {
  key: string;
  label: string;
  type: FieldType;
  options?: FieldOption[];
  required?: boolean;
}

export interface ReferenceDataShape {
  sucursales: string[];
  ingredientes: Array<{ id: number; ingrediente_id: string; nombre: string; proveedor: string; unidad_base: string }>;
  proveedores: Array<{ id: number; nombre: string }>;
  unidades: string[];
  semanas: string[];
  tiposFormato: string[];
  formatosCompra: string[];
}

export const DATASETS = [
  { key: "ingredients", label: "Ingredientes" },
  { key: "inventory", label: "Inventario" },
  { key: "consumption", label: "Consumo" },
  { key: "purchase_orders", label: "Ordenes" },
];

const booleanOptions = [
  { value: "true", label: "Si" },
  { value: "false", label: "No" },
];

function options(values: string[]): FieldOption[] {
  return values.map((value) => ({ value, label: value }));
}

function providerOptions(reference: ReferenceDataShape): FieldOption[] {
  return reference.proveedores.map((provider) => ({ value: String(provider.id), label: provider.nombre }));
}

function providerNameOptions(reference: ReferenceDataShape): FieldOption[] {
  return reference.proveedores.map((provider) => ({ value: provider.nombre, label: provider.nombre }));
}

function ingredientOptions(reference: ReferenceDataShape): FieldOption[] {
  return reference.ingredientes.map((ingredient) => ({
    value: String(ingredient.id),
    label: `${ingredient.nombre} (${ingredient.ingrediente_id})`,
  }));
}

function ingredientExternalOptions(reference: ReferenceDataShape): FieldOption[] {
  return reference.ingredientes.map((ingredient) => ({
    value: ingredient.ingrediente_id,
    label: `${ingredient.nombre} (${ingredient.ingrediente_id})`,
  }));
}

export function tableColumns(dataset: string, reference: ReferenceDataShape): ColumnConfig[] {
  if (dataset === "ingredients") {
    return [
      { key: "external_id", label: "ID ingrediente", type: "text" },
      { key: "name", label: "Nombre", type: "text" },
      { key: "supplier_id", label: "Proveedor", type: "select", options: providerOptions(reference) },
      { key: "base_unit", label: "Unidad", type: "select", options: options(reference.unidades) },
      { key: "purchase_format", label: "Formato", type: "select", options: options(reference.formatosCompra) },
      { key: "conversion_factor", label: "Factor", type: "number" },
      { key: "is_perishable", label: "Perecedero", type: "boolean", options: booleanOptions },
      { key: "estimated_unit_cost", label: "Costo", type: "number" },
    ];
  }
  if (dataset === "consumption") {
    return [
      { key: "branch", label: "Sucursal", type: "select", options: options(reference.sucursales) },
      { key: "ingredient_id", label: "Ingrediente", type: "select", options: ingredientOptions(reference) },
      { key: "week", label: "Semana", type: "select", options: options(reference.semanas) },
      { key: "quantity_base_unit", label: "Cantidad", type: "number" },
    ];
  }
  if (dataset === "inventory") {
    return [
      { key: "branch", label: "Sucursal", type: "select", options: options(reference.sucursales) },
      { key: "ingredient_id", label: "Ingrediente", type: "select", options: ingredientOptions(reference) },
      { key: "quantity_base_unit", label: "Cantidad actual", type: "number" },
    ];
  }
  return [
    { key: "branch", label: "Sucursal", type: "select", options: options(reference.sucursales) },
    { key: "ingredient_id", label: "Ingrediente", type: "select", options: ingredientOptions(reference) },
    { key: "quantity_formats", label: "Formatos", type: "number" },
  ];
}

export function formColumns(dataset: string, reference: ReferenceDataShape): ColumnConfig[] {
  if (dataset === "ingredients") {
    return [
      { key: "ingrediente_id", label: "ID ingrediente", type: "text", required: true },
      { key: "nombre", label: "Nombre", type: "text", required: true },
      {
        key: "proveedor",
        label: "Proveedor",
        type: "select",
        options: [...providerNameOptions(reference), { value: "__new__", label: "+ Agregar nuevo proveedor" }],
        required: true,
      },
      { key: "unidad_base", label: "Unidad", type: "select", options: options(reference.unidades), required: true },
      { key: "tipo_formato", label: "Tipo de formato", type: "select", options: options(reference.tiposFormato), required: true },
      { key: "cantidad_formato", label: "Cantidad por formato", type: "number", required: true },
      { key: "unidad_formato", label: "Unidad del formato", type: "select", options: options(reference.unidades), required: true },
      { key: "es_perecedero", label: "Perecedero", type: "boolean", options: booleanOptions, required: true },
      { key: "costo_unitario_estimado", label: "Costo unitario", type: "number" },
    ];
  }
  if (dataset === "consumption") {
    return [
      { key: "sucursal", label: "Sucursal", type: "select", options: options(reference.sucursales), required: true },
      { key: "ingrediente_id", label: "Ingrediente", type: "select", options: ingredientExternalOptions(reference), required: true },
      { key: "semana", label: "Semana", type: "select", options: options(reference.semanas), required: true },
      { key: "consumo_unidad_base", label: "Cantidad consumida", type: "number", required: true },
    ];
  }
  if (dataset === "inventory") {
    return [
      { key: "sucursal", label: "Sucursal", type: "select", options: options(reference.sucursales), required: true },
      { key: "ingrediente_id", label: "Ingrediente", type: "select", options: ingredientExternalOptions(reference), required: true },
      { key: "stock_actual_unidad_base", label: "Cantidad actual", type: "number", required: true },
    ];
  }
  return [
    { key: "sucursal", label: "Sucursal", type: "select", options: options(reference.sucursales), required: true },
    { key: "ingrediente_id", label: "Ingrediente", type: "select", options: ingredientExternalOptions(reference), required: true },
    { key: "cantidad_formatos", label: "Cantidad formatos", type: "number", required: true },
  ];
}

export function buildCreatePayload(dataset: string, values: Record<string, string>) {
  if (dataset !== "ingredients") return values;
  const quantity = Number(values.cantidad_formato || 0);
  const unit = values.unidad_formato;
  return {
    ingrediente_id: values.ingrediente_id,
    nombre: values.nombre,
    proveedor: values.proveedor === "__new__" ? values.proveedor_nuevo : values.proveedor,
    unidad_base: values.unidad_base,
    formato_compra: `${values.tipo_formato} ${quantity} ${unit}`,
    unidad_base_por_formato: String(quantity),
    es_perecedero: values.es_perecedero,
    costo_unitario_estimado: values.costo_unitario_estimado,
  };
}
