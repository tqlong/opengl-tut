from OpenGLContext import testingcontext
from OpenGLContext.arrays import *
from OpenGLContext.events.timer import Timer
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import vbo

BaseContext = testingcontext.getInteractive()


class TestContext (BaseContext):
    def OnInit(self):
        VERTEX_SHADER = shaders.compileShader("""
        varying vec4 baseColor;
        uniform float tween;
        attribute vec3 position;
        attribute vec3 tweened;
        attribute vec3 color;
        void main() {
            gl_Position = gl_ModelViewProjectionMatrix * mix(
                vec4(position, 1.0),
                vec4(tweened, 1.0),
                tween
            );
            baseColor = vec4(color, 1.0);
        }""", GL_VERTEX_SHADER)

        FRAGMENT_SHADER = shaders.compileShader("""
        varying vec4 baseColor;
        void main() {
            gl_FragColor = baseColor;
        }""", GL_FRAGMENT_SHADER)

        self.shader = shaders.compileProgram(VERTEX_SHADER, FRAGMENT_SHADER)

        self.vbo = vbo.VBO(
            array([
                [0, 1, 0, 1, 3, 0,  0, 1, 0],
                [-1, -1, 0, -1, -1, 0,  1, 1, 0],
                [1, -1, 0, 1, -1, 0, 0, 1, 1],
                [2, -1, 0, 2, -1, 0, 1, 0, 0],
                [4, -1, 0, 4, -1, 0, 0, 1, 0],
                [4, 1, 0, 4, 9, 0, 0, 0, 1],
                [2, -1, 0, 2, -1, 0, 1, 0, 0],
                [4, 1, 0, 1, 3, 0, 0, 0, 1],
                [2, 1, 0, 1, -1, 0, 0, 1, 1],
            ], 'f')
        )

        self.locations = {
            'position': glGetAttribLocation(self.shader, 'position'),
            'tweened': glGetAttribLocation(self.shader, 'tweened'),
            'color': glGetAttribLocation(self.shader, 'color'),
            'tween': glGetUniformLocation(self.shader, 'tween'),
        }

        self.timer = Timer(duration=2.0, repeating=1)
        self.timer.addEventHandler("fraction", self.OnTimerFraction)
        self.timer.register(self)
        self.timer.start()

    def Render(self, mode):
        BaseContext.Render(self, mode)
        shaders.glUseProgram(self.shader)
        # set GPU uniform (global) variable tween to have value of self.tween_fraction
        glUniform1f(self.locations['tween'], self.tween_fraction)

        try:
            self.vbo.bind()
            try:
                glEnableVertexAttribArray(self.locations['position'])
                glEnableVertexAttribArray(self.locations['tweened'])
                glEnableVertexAttribArray(self.locations['color'])

                # set data (position, tweened, color) using self.vbo array
                stride = 9*4
                glVertexAttribPointer(
                    self.locations['position'], 3, GL_FLOAT, False, stride, self.vbo)
                glVertexAttribPointer(
                    self.locations['tweened'], 3, GL_FLOAT, False, stride, self.vbo+12)
                glVertexAttribPointer(
                    self.locations['color'], 3, GL_FLOAT, False, stride, self.vbo+24)

                glDrawArrays(GL_TRIANGLES, 0, 9)
            finally:
                self.vbo.unbind()
                glDisableVertexAttribArray(self.locations['position'])
                glDisableVertexAttribArray(self.locations['tweened'])
                glDisableVertexAttribArray(self.locations['color'])
        finally:
            shaders.glUseProgram(0)

    tween_fraction = 0.0

    def OnTimerFraction(self, event):
        frac = event.fraction()
        if frac > 0.5:
            frac = 1.0-frac
        frac *= 2
        self.tween_fraction = frac
        self.triggerRedraw()


if __name__ == "__main__":
    TestContext.ContextMainLoop()
