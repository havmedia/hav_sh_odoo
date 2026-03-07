{
    'name': 'HAV - HAV.sh Subscription Integration',
    'summary': 'HAV - HAV.sh Subscription Integration',
    'description': 'Links subscription products with HAV.sh provisioning templates for automatic instance provisioning.',
    'author': 'HAV Media GmbH',
    'category': 'Custom',
    'version': '18.0.1.0.0',
    'data': [
        'views/product_template.xml',
        'views/sale_order.xml',
    ],
    'depends': [
        'hav_sh_base',
        'sale_subscription',
    ],
}
