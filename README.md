# 1. Bingx-API

This is yet another library to access Bingx's API.

## 1.1. Contribution

⭐️ Hopefully you have starred the project ⭐️

You can contribute to the project in two ways :

**Code and documentation** : pull requests are welcome !

**Feedback** : feel free to open an issue or send me a message if you have a feedback or question.

## 1.2. Installation

```bash
# INSTALL
pip install bingx-api

# UPGRADE
pip install --no-cache-dir --upgrade bingx-api

# UNINSTALL
pip uninstall bingx-api
```

## 1.3. Features

|**Module**|**Feature(s)**|
|:-|:-|
|bingx_api.future.rest.create_order_list|Create order list.|
|bingx_api.future.rest.create_order|Create one order.|
|bingx_api.future.rest.delete_all_order|Delete all orders.|
|bingx_api.future.rest.delete_order_list|Create order list.|
|bingx_api.future.rest.delete_order|Delete one order.|
|bingx_api.future.rest.read_commission_rate|Read commission rate information.|
|bingx_api.future.rest.read_contract_list|Read all contracts information.|
|bingx_api.future.rest.read_funding_rate|Read funding rate information.|
|bingx_api.future.rest.read_kline|Read KLine.|
|bingx_api.future.rest.read_last_price|Read a future's last price.|
|bingx_api.future.rest.read_leverage|Read leverage information.|
|bingx_api.future.rest.read_margin_tiered|Read margin tiered information.|
|bingx_api.future.rest.read_open_order_list|Read all opened orders.|
|bingx_api.future.rest.read_order_list|Read order list.|
|bingx_api.future.rest.read_order|Read one order information.|
|bingx_api.future.rest.read_position_list|Read position list.|
|bingx_api.future.rest.update_position_margin|Update margin on a future.|
|bingx_api.future.ws.delete_listen_key|Delete listen key.|
|bingx_api.future.ws.read_listen_key|Read listen key necessary to establish a websocket connection.|
|bingx_api.future.ws.stream_account|Read account information in real-time.|
|bingx_api.future.ws.stream_channel|Generic webservice consummer.|
|bingx_api.future.ws.stream_last_price|Read future's last price in real-time|
|bingx_api.future.ws.update_listen_key|Refresh listen key necessary to establish a websocket connection.|
|bingx_api.future.ws.valid_listen_key|Maintain a valid listen key necessary to establish a websocket connection.|

## Contributing

We welcome contributions to Bingx-API. If you find any issues or have suggestions for improvements, please open an issue or submit a pull request.

## License

Bingx-API is licensed under the BSD-3-Clause license. See the [LICENSE](LICENSE) file for more information.