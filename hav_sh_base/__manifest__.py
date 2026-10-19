{
    'name': 'HAV - HAV.sh Integration',
    'summary': 'HAV - HAV.sh Integration',
    'description': 'HAV - HAV.sh Integration',
    'author': 'HAV Media GmbH',
    'category': 'Custom',
    'version': '18.0.1.0.2',
    'data': [
        'views/res_company.xml',

        'views/havsh_odoo.xml',
        'views/havsh_server.xml',
        'views/havsh_provisioning_template.xml',
        'views/havsh_provisioning_job.xml',

        'views/menu_items.xml',
        'data/ir.model.access.csv',
        'data/havsh_odoo_server_actions.xml',
        'data/havsh_provisioning_template_server_actions.xml',
        'data/ir_cron.xml',
    ],
    'depends': [
        'queue_job'
    ],
    "external_dependencies": {"python" : ["python-slugify"]}
}
