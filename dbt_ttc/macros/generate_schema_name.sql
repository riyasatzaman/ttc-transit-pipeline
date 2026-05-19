{# Override dbt's default schema-name generator.

   Default behavior produces "<target.schema>_<custom_schema>" (e.g. STAGING_STAGING),
   which is great for multi-developer setups but noisy for a single-environment
   portfolio project. This override uses custom_schema_name verbatim when set,
   falling back to target.schema otherwise.

   Docs: https://docs.getdbt.com/docs/build/custom-schemas
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
