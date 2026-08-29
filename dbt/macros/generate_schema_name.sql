{#
    Write to literal schemas.

    dbt's default concatenates the target schema with the custom one, so a model
    configured `+schema: GOLD` against target schema SILVER lands in SILVER_GOLD.
    This override makes `+schema:` mean exactly what it says.

    Without this, Beat 4's one-shot builds Gold into the wrong schema and the
    Streamlit app finds nothing. See CLAUDE.md → Naming.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- if custom_schema_name is none -%}
        {{ target.schema }}
    {%- else -%}
        {{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
