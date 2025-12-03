const path = require('path');

module.exports = {
  entry: './src/index.tsx',
  output: {
    filename: 'index.js',
    path: path.resolve(__dirname, '../tensorboard_flight/static'),
    library: {
      name: 'tensorboard_flight',
      type: 'umd',
    },
  },
  resolve: {
    extensions: ['.ts', '.tsx', '.js', '.jsx'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
    },
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader'],
      },
    ],
  },
  // Removed externals - bundle React with the app for reliability
  // externals: {
  //   'react': 'React',
  //   'react-dom': 'ReactDOM',
  // },
  mode: 'production',
  devtool: 'source-map',
};
